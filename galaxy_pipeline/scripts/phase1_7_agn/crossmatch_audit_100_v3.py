import pandas as pd
import numpy as np
import time
import json
from datetime import datetime
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- CONFIGURATION ---
SIMBAD_RADIUS_ARCSEC = 1.0
TEST_ROWS = 100
INPUT_FILE = "gaia_phase1_sample.csv"

simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype')

# --- ROBUST TAXONOMY MAPPER (Substring Matching) ---
def map_confidence_tier(otype):
    if pd.isna(otype):
        return 'Tier_0_Unknown'
    otype_upper = str(otype).strip().upper()
    
    # Substring matching survives catalog variations (e.g., "EmG", "EmG*", "GiG")
    if any(x in otype_upper for x in ["AGN", "QSO", "GAL", "EMG", "GRG", "LSB", "SEYFERT", "BCG", "GXY"]):
        return 'Tier_1_Extragalactic_High'
    elif any(x in otype_upper for x in ["AG?", "G?", "CANDIDATE"]):
        return 'Tier_2_Extragalactic_Candidate'
    elif any(x in otype_upper for x in ["STAR", "PM*", "WD*", "Y*O", "IR*"]):
        return 'Tier_1_Stellar_High'
    else:
        return f'Tier_3_Ambiguous_{otype}'

def audit_simbad_labels(df):
    logging.info(f"Starting SIMBAD audit for {len(df)} sources...")
    
    # Initialize columns
    df['simbad_main_id'] = None
    df['simbad_otype_raw'] = None
    df['simbad_sep_arcsec'] = None
    df['simbad_status'] = 'Pending'
    df['label_confidence_tier'] = 'Pending'
    
    # Provenance columns
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
                    otype = str(result['otype'][0]).strip()
                    df.at[idx, 'simbad_otype_raw'] = otype
                    df.at[idx, 'label_confidence_tier'] = map_confidence_tier(otype)
                
                # DEBUG: Check RA/Dec format on first match
                if idx == 0 and 'ra' in result.colnames and 'dec' in result.colnames:
                    logging.info(f"DEBUG RA/Dec types: RA={type(result['ra'][0])} val={result['ra'][0]}, DEC={type(result['dec'][0])} val={result['dec'][0]}")
                    
                # Calculate angular separation (Robust parsing for float or sexagesimal string)
                try:
                    ra_val = float(result['ra'][0])
                    dec_val = float(result['dec'][0])
                    matched_coord = SkyCoord(ra=ra_val*u.deg, dec=dec_val*u.deg)
                except (ValueError, TypeError):
                    # Fallback to sexagesimal string parsing
                    matched_coord = SkyCoord(result['ra'][0], result['dec'][0], unit=(u.hourangle, u.deg))
                
                sep = coord.separation(matched_coord)
                df.at[idx, 'simbad_sep_arcsec'] = round(sep.arcsec, 4)
                
            else:
                df.at[idx, 'simbad_status'] = 'NoMatch'
                df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
        except Exception as e:
            logging.warning(f"Row {idx}: SIMBAD Exception -> {e}")
            df.at[idx, 'simbad_status'] = 'Error'
            df.at[idx, 'label_confidence_tier'] = 'Error'

        time.sleep(0.3) # Polite rate limiting

    return df

if __name__ == "__main__":
    try:
        logging.info(f"Loading {INPUT_FILE}...")
        full_df = pd.read_csv(INPUT_FILE)
        df = full_df.head(TEST_ROWS).copy()
        logging.info(f"Restricted to first {len(df)} rows for audit.")
        
        logging.info("Running SIMBAD audit...")
        audited_df = audit_simbad_labels(df)
        
        # 1. Save Results CSV
        output_csv = "crossmatch_audit_100_results_v3.csv"
        audited_df.to_csv(output_csv, index=False)
        logging.info(f"Saved audit results to {output_csv}")
        
        # 2. Calculate Statistics
        total = len(audited_df)
        matches = audited_df[audited_df["simbad_status"] == 'Match'].shape[0]
        
        # 3. Create and Save Enhanced Audit JSON
        audit = {
            "rows_tested": int(total),
            "matches": int(matches),
            "match_rate": float(matches / total) if total > 0 else 0.0,
            "tier_distribution": audited_df["label_confidence_tier"].value_counts().to_dict(),
            "otype_distribution": audited_df["simbad_otype_raw"].value_counts().to_dict() # NEW: Raw type counts
        }
        with open("crossmatch_audit_100_v3.json", "w") as f:
            json.dump(audit, f, indent=2)
        logging.info("Saved crossmatch_audit_100_v3.json")
        
        # 4. Print Summary
        print("\n" + "="*60)
        print("SIMBAD AUDIT STATISTICS (N=100)")
        print("="*60)
        print(f"Total Rows Tested: {total}")
        print(f"Match Rate:        {audit['match_rate']:.2%} ({matches}/{total})")
        
        print("\n" + "="*60)
        print("LABEL CONFIDENCE TIER DISTRIBUTION:")
        print("="*60)
        print(audited_df['label_confidence_tier'].value_counts().to_string())
        
        print("\n" + "="*60)
        print("UNIQUE SIMBAD OTYPEs FOUND:")
        print("="*60)
        unique_otypes = audited_df['simbad_otype_raw'].dropna().unique()
        for otype in unique_otypes:
            count = (audited_df['simbad_otype_raw'] == otype).sum()
            print(f"  '{otype}' : {count} occurrence(s)")
            
        print("\n" + "="*60)
        print("SAMPLE OF HIGH-CONFIDENCE MATCHES:")
        print("="*60)
        high_conf = audited_df[audited_df['label_confidence_tier'].str.contains('Tier_1')]
        if len(high_conf) > 0:
            cols = ['source_id', 'simbad_main_id', 'simbad_otype_raw', 'simbad_sep_arcsec', 'label_confidence_tier']
            print(high_conf[cols].head(10).to_string(index=False))
        else:
            print("  (No Tier 1 matches in this sample)")
        print("="*60)
        
    except FileNotFoundError:
        logging.error(f"Could not find '{INPUT_FILE}'.")