import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timezone
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- CONFIGURATION ---
SIMBAD_RADIUS_ARCSEC = 1.0
TEST_ROWS = 500
INPUT_FILE = "gaia_phase1_sample.csv"
PIPELINE_VERSION = "crossmatch_audit_500_final_v3"

simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype')

# --- FROZEN TAXONOMY MAPPER ---
HIGH_EXTRAGALACTIC = {
    "AGN", "QSO", "EMG", "GRG", "LSB", "BCG", "GXY", "G", 
    "SY1", "SY2", "GIG", "GIC", "POG"
}
CANDIDATE_EXTRAGALACTIC = {"AG?", "G?", "CANDIDATE"}
HIGH_STELLAR = {"STAR", "PM*", "WD*", "Y*O", "IR*", "WR*", "*"}

def map_confidence_tier(otype):
    otype_upper = str(otype).strip().upper()
    
    if otype_upper in HIGH_EXTRAGALACTIC:
        return 'Tier_1_Extragalactic_High'
    elif otype_upper in CANDIDATE_EXTRAGALACTIC:
        return 'Tier_2_Extragalactic_Candidate'
    elif otype_upper == "HII":
        return 'Tier_2_Review_HII'
    elif otype_upper in HIGH_STELLAR:
        return 'Tier_1_Stellar_High'
    else:
        return f'Tier_3_Ambiguous_{otype}'

def audit_simbad_labels(df):
    logging.info(f"Starting SIMBAD audit for {len(df)} sources...")
    
    df['simbad_main_id'] = None
    df['simbad_otype_raw'] = None
    df['simbad_sep_arcsec'] = None
    df['crossmatch_quality'] = None
    df['simbad_status'] = 'Pending'
    df['label_confidence_tier'] = 'Pending'
    df['catalog_source'] = 'SIMBAD'
    df['query_radius_arcsec'] = SIMBAD_RADIUS_ARCSEC

    for idx, row in df.iterrows():
        ra = row['ra']
        dec = row['dec']
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        
        try:
            result = simbad_custom.query_region(coord, radius=SIMBAD_RADIUS_ARCSEC*u.arcsec)
            if result is not None and len(result) > 0:
                df.at[idx, 'simbad_status'] = 'Match'
                
                if 'main_id' in result.colnames:
                    df.at[idx, 'simbad_main_id'] = str(result['main_id'][0]).strip()
                
                if 'otype' in result.colnames:
                    # FIX 2: Handle empty OTYPE explicitly
                    otype_raw = result['otype'][0]
                    otype = str(otype_raw).strip() if pd.notna(otype_raw) else ""
                    
                    if not otype:
                        df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
                    else:
                        df.at[idx, 'simbad_otype_raw'] = otype
                        df.at[idx, 'label_confidence_tier'] = map_confidence_tier(otype)
                
                try:
                    ra_val = float(result['ra'][0])
                    dec_val = float(result['dec'][0])
                    matched_coord = SkyCoord(ra=ra_val*u.deg, dec=dec_val*u.deg)
                except (ValueError, TypeError):
                    matched_coord = SkyCoord(result['ra'][0], result['dec'][0], unit=(u.hourangle, u.deg))
                
                sep = coord.separation(matched_coord)
                sep_arcsec = float(sep.arcsec) # Save as pure float
                
                df.at[idx, 'simbad_sep_arcsec'] = sep_arcsec
                
                if sep_arcsec <= 0.2:
                    df.at[idx, 'crossmatch_quality'] = 'Excellent'
                elif sep_arcsec <= 0.5:
                    df.at[idx, 'crossmatch_quality'] = 'Good'
                else:
                    df.at[idx, 'crossmatch_quality'] = 'Review'
            else:
                df.at[idx, 'simbad_status'] = 'NoMatch'
                df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
        except Exception as e:
            logging.warning(f"Row {idx}: SIMBAD Exception -> {e}")
            df.at[idx, 'simbad_status'] = 'Error'
            df.at[idx, 'label_confidence_tier'] = 'Error'

        if (idx + 1) % 50 == 0:
            logging.info(f"Processed {idx+1}/{len(df)} sources...")
            
        time.sleep(0.3)

    return df

if __name__ == "__main__":
    try:
        logging.info(f"Loading {INPUT_FILE}...")
        full_df = pd.read_csv(INPUT_FILE)
        
        # FIX 4: Protect against missing columns
        required_columns = ["ra", "dec"]
        missing = [c for c in required_columns if c not in full_df.columns]
        if missing:
            raise ValueError(f"Missing required columns in {INPUT_FILE}: {missing}")
            
        df = full_df.head(TEST_ROWS).copy()
        logging.info(f"Restricted to first {len(df)} rows for audit.")
        
        logging.info("Running SIMBAD audit...")
        audited_df = audit_simbad_labels(df)
        
        output_csv = "crossmatch_audit_500_final.csv"
        audited_df.to_csv(output_csv, index=False)
        logging.info(f"Saved audit results to {output_csv}")
        
        total = len(audited_df)
        matches = audited_df[audited_df["simbad_status"] == 'Match'].shape[0]
        
        # FIX 1 & 3: Modern UTC timestamp and quality distribution
        status_distribution = audited_df["simbad_status"].value_counts().to_dict()
        quality_distribution = audited_df["crossmatch_quality"].value_counts().to_dict()
        
        audit = {
            "pipeline_version": PIPELINE_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "gaia_file": INPUT_FILE,
            "test_rows": int(total),
            "radius_arcsec": SIMBAD_RADIUS_ARCSEC,
            "matches": int(matches),
            "match_rate": float(matches / total) if total > 0 else 0.0,
            "status_distribution": {str(k): int(v) for k, v in status_distribution.items()},
            "crossmatch_quality_distribution": {str(k): int(v) for k, v in quality_distribution.items()},
            "tier_distribution": {str(k): int(v) for k, v in audited_df["label_confidence_tier"].value_counts().to_dict().items()},
            "otype_distribution": {str(k): int(v) for k, v in audited_df["simbad_otype_raw"].value_counts().to_dict().items()}
        }
        
        with open("crossmatch_audit_500_final.json", "w") as f:
            json.dump(audit, f, indent=2)
        logging.info("Saved crossmatch_audit_500_final.json")
        
        print("\n" + "="*60)
        print("SIMBAD AUDIT STATISTICS (N=500)")
        print("="*60)
        print(f"Total Rows Tested: {total}")
        print(f"Match Rate:        {audit['match_rate']:.2%} ({matches}/{total})")
        
        print("\n" + "="*60)
        print("QUERY STATUS DISTRIBUTION:")
        print("="*60)
        for status, count in audit['status_distribution'].items():
            print(f"  {status}: {count} ({count/total:.2%})")
            
        print("\n" + "="*60)
        print("LABEL CONFIDENCE TIER DISTRIBUTION:")
        print("="*60)
        print(audited_df['label_confidence_tier'].value_counts().to_string())
        
        print("\n" + "="*60)
        print("TOP 10 UNIQUE SIMBAD OTYPEs FOUND:")
        print("="*60)
        top_otypes = audited_df['simbad_otype_raw'].value_counts().head(10)
        for otype, count in top_otypes.items():
            print(f"  '{otype}' : {count} occurrence(s)")
            
        print("\n" + "="*60)
        print("CONTAMINATION CHECK (Stellar High):")
        print("="*60)
        stellar = audited_df[audited_df['label_confidence_tier'] == 'Tier_1_Stellar_High']
        if len(stellar) > 0:
            print(f"Found {len(stellar)} stellar contaminants. Sample:")
            display_df = stellar[['source_id', 'simbad_main_id', 'simbad_otype_raw', 'simbad_sep_arcsec']].copy()
            display_df['simbad_sep_arcsec'] = display_df['simbad_sep_arcsec'].round(4)
            print(display_df.head(5).to_string(index=False))
        else:
            print("  (No stellar contaminants found in this sample)")
        print("="*60)
        
    except FileNotFoundError:
        logging.error(f"Could not find '{INPUT_FILE}'.")
    except ValueError as e:
        logging.error(str(e))