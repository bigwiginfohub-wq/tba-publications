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
TEST_ROWS = 100  # Scaled up from 20
INPUT_FILE = "gaia_phase1_sample.csv"

simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype')

# --- TAXONOMY MAPPER ---
# Based on real SIMBAD OTYPE definitions
EXTRAGALACTIC_HIGH = {'AGN', 'EmG', 'GrG', 'LSB', 'G', 'GiG', 'BCG', 'QSO', 'Sy1', 'Sy2', 'Seyfert', 'Gxy'}
EXTRAGALACTIC_CANDIDATE = {'AG?', 'G?', 'Candidate'}
STELLAR_HIGH = {'Star', 'PM*', 'WD*', 'Y*O', 'IR*'}

def map_confidence_tier(otype):
    if pd.isna(otype):
        return 'Tier_0_Unknown'
    otype_clean = str(otype).strip()
    if otype_clean in EXTRAGALACTIC_HIGH:
        return 'Tier_1_Extragalactic_High'
    elif otype_clean in EXTRAGALACTIC_CANDIDATE:
        return 'Tier_2_Extragalactic_Candidate'
    elif otype_clean in STELLAR_HIGH:
        return 'Tier_1_Stellar_High' # Important: catches false positives!
    else:
        return f'Tier_3_Ambiguous_{otype_clean}'

def audit_simbad_labels(df):
    logging.info(f"Starting SIMBAD audit for {len(df)} sources...")
    
    df['simbad_main_id'] = None
    df['simbad_otype_raw'] = None
    df['simbad_sep_arcsec'] = None
    df['simbad_status'] = 'Pending'
    df['label_confidence_tier'] = 'Pending'

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
                    
                # Calculate angular separation
                try:
                    matched_coord = SkyCoord(ra=result['ra'][0]*u.deg, dec=result['dec'][0]*u.deg)
                    sep = coord.separation(matched_coord)
                    df.at[idx, 'simbad_sep_arcsec'] = round(sep.arcsec, 4)
                except Exception:
                    pass
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
        
        # Save Results
        output_csv = "crossmatch_audit_100_results.csv"
        audited_df.to_csv(output_csv, index=False)
        logging.info(f"Saved audit results to {output_csv}")
        
        # Calculate Statistics
        total = len(audited_df)
        matches = audited_df[audited_df["simbad_status"] == 'Match'].shape[0]
        
        print("\n" + "="*60)
        print("SIMBAD AUDIT STATISTICS (N=100)")
        print("="*60)
        print(f"Total Rows Tested: {total}")
        print(f"Match Rate:        {matches/total:.2%} ({matches}/{total})")
        
        print("\n" + "="*60)
        print("LABEL CONFIDENCE TIER DISTRIBUTION:")
        print("="*60)
        print(audited_df['label_confidence_tier'].value_counts().to_string())
        
        print("\n" + "="*60)
        print("UNIQUE SIMBAD OTYPEs FOUND:")
        print("="*60)
        unique_otypes = audited_df['simbad_otype_raw'].dropna().unique()
        for otype in unique_otypes:
            count = (audited_df['simbad_otype_raw'] == otype).sum mean() # Wait, sum is better
            count = (audited_df['simbad_otype_raw'] == otype).sum()
            print(f"  '{otype}' : {count} occurrence(s)")
            
                print("\n" + "="*60)
        print("UNIQUE SIMBAD OTYPEs FOUND:")
        print("="*60)
        unique_otypes = audited_df['simbad_otype_raw'].dropna().unique()
        for otype in unique_otypes:
            count = (audited_df['simbad_otype_raw'] == otype).sum()
            print(f"  '{otype}' : {count} occurrence(s)")