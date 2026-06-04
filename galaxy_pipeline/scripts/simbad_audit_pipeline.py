import pandas as pd
import numpy as np
import time
import json
import sqlite3
from datetime import datetime, timezone
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- CONFIGURATION (Pre-configured for the 186 new candidates) ---
SIMBAD_RADIUS_ARCSEC = 1.0
TEST_ROWS = 21  # <-- CHANGE THIS
INPUT_FILE = "gaia_phase1_final_candidates.csv" # <-- CHANGE THIS
PIPELINE_VERSION = "crossmatch_audit_final_candidates" # <-- CHANGE THIS
CACHE_DB = "simbad_cache.db"

simbad_custom = Simbad()
simbad_custom.TIMEOUT = 30
simbad_custom.add_votable_fields('otype')

# --- FROZEN TAXONOMY MAPPER ---
HIGH_EXTRAGALACTIC = {
    "AGN", "QSO", "EMG", "GRG", "LSB", "BCG", "GXY", "G", 
    "SY1", "SY2", "GIG", "GIC", "POG", "GIP"
}
CANDIDATE_EXTRAGALACTIC = {"AG?", "G?", "CANDIDATE"}
HIGH_STELLAR = {
    "STAR", "PM*", "WD*", "Y*O", "IR*", "WR*", "*", 
    "RR*", "EB*", "SG*", "CL*"
}

def map_confidence_tier(otype):
    otype_upper = str(otype).strip().upper()
    if otype_upper in HIGH_EXTRAGALACTIC:
        return 'Tier_1_Extragalactic_High'
    elif otype_upper in CANDIDATE_EXTRAGALACTIC:
        return 'Tier_2_Extragalactic_Candidate'
    elif otype_upper == "HII":
        return 'Tier_2_Review_HII'
    elif otype_upper == "X":
        return 'Tier_2_Review_Xray'
    elif otype_upper == "BIC":
        return 'Tier_2_Review_Bipolar'
    elif otype_upper in HIGH_STELLAR:
        return 'Tier_1_Stellar_High'
    else:
        return f'Tier_3_Ambiguous_{otype}'

# --- OPTIMIZED CACHING ENGINE ---
def init_cache(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS simbad_cache (
            ra REAL, dec REAL, radius REAL,
            result_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ra, dec, radius)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache ON simbad_cache(ra, dec, radius)')
    conn.commit()
    return conn

def get_cached_result(conn, ra_key, dec_key, radius):
    cursor = conn.cursor()
    cursor.execute("SELECT result_json FROM simbad_cache WHERE ra=? AND dec=? AND radius=?", (ra_key, dec_key, radius))
    row = cursor.fetchone()
    return json.loads(row[0]) if row else None

def cache_result(conn, ra_key, dec_key, radius, result_dict):
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO simbad_cache (ra, dec, radius, result_json) VALUES (?, ?, ?, ?)', 
                   (ra_key, dec_key, radius, json.dumps(result_dict)))

def process_match(df, idx, result_dict, coord):
    df.at[idx, 'simbad_status'] = 'Match'
    df.at[idx, 'simbad_match_count'] = result_dict.get('_length', 1)
    
    if 'main_id' in result_dict:
        df.at[idx, 'simbad_main_id'] = str(result_dict['main_id'][0]).strip()
    
    if 'otype' in result_dict:
        otype_raw = result_dict['otype'][0]
        otype = str(otype_raw).strip() if pd.notna(otype_raw) else ""
        if not otype:
            df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
        else:
            df.at[idx, 'simbad_otype_raw'] = otype
            df.at[idx, 'label_confidence_tier'] = map_confidence_tier(otype)
    
    try:
        ra_val = float(result_dict['ra'][0])
        dec_val = float(result_dict['dec'][0])
        matched_coord = SkyCoord(ra=ra_val*u.deg, dec=dec_val*u.deg)
    except (ValueError, TypeError):
        matched_coord = SkyCoord(str(result_dict['ra'][0]), str(result_dict['dec'][0]), unit=(u.hourangle, u.deg))
    
    sep_arcsec = float(coord.separation(matched_coord).arcsec)
    df.at[idx, 'simbad_sep_arcsec'] = sep_arcsec
    
    if sep_arcsec <= 0.2: df.at[idx, 'crossmatch_quality'] = 'Excellent'
    elif sep_arcsec <= 0.5: df.at[idx, 'crossmatch_quality'] = 'Good'
    elif sep_arcsec <= 0.8: df.at[idx, 'crossmatch_quality'] = 'Review'
    else: df.at[idx, 'crossmatch_quality'] = 'LowConfidence'

def audit_simbad_labels(df, conn):
    logging.info(f"Starting SIMBAD audit for {len(df)} sources...")
    
    for col in ['simbad_main_id', 'simbad_otype_raw', 'simbad_sep_arcsec', 'crossmatch_quality']:
        df[col] = None
    df['simbad_match_count'] = 0
    df['simbad_status'] = 'Pending'
    df['label_confidence_tier'] = 'Pending'
    df['catalog_source'] = 'SIMBAD'
    df['query_radius_arcsec'] = SIMBAD_RADIUS_ARCSEC
    df['from_cache'] = False

    for idx, row in df.iterrows():
        ra, dec = row['ra'], row['dec']
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        ra_key, dec_key = round(ra, 6), round(dec, 6)
        
        cached_data = get_cached_result(conn, ra_key, dec_key, SIMBAD_RADIUS_ARCSEC)
        
        if cached_data is not None:
            df.at[idx, 'from_cache'] = True
            if cached_data.get("_status") == "NoMatch":
                df.at[idx, 'simbad_status'] = 'NoMatch'
                df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
            else:
                process_match(df, idx, cached_data, coord)
        else:
            df.at[idx, 'from_cache'] = False
            try:
                result = simbad_custom.query_region(coord, radius=SIMBAD_RADIUS_ARCSEC*u.arcsec)
                if result is not None and len(result) > 0:
                    result_dict = {'_length': len(result)}
                    for col in result.colnames:
                        values = [str(v.item()) if hasattr(v, "item") else (str(v) if isinstance(v, bytes) else v) for v in result[col]]
                        result_dict[col] = values
                    process_match(df, idx, result_dict, coord)
                else:
                    result_dict = {"_status": "NoMatch", "_length": 0}
                    df.at[idx, 'simbad_status'] = 'NoMatch'
                    df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
                
                cache_result(conn, ra_key, dec_key, SIMBAD_RADIUS_ARCSEC, result_dict)
                time.sleep(0.2)
            except Exception as e:
                logging.warning(f"Row {idx}: SIMBAD Network Exception -> {e}")
                df.at[idx, 'simbad_status'] = 'Error'
                df.at[idx, 'label_confidence_tier'] = 'Error'

        if (idx + 1) % 50 == 0:
            conn.commit()
            logging.info(f"Processed {idx+1}/{len(df)} sources... (Cache hits: {df['from_cache'].sum()})")
            
    conn.commit()
    return df

if __name__ == "__main__":
    try:
        logging.info(f"Loading {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE).head(TEST_ROWS).copy()
        logging.info(f"Loaded {len(df)} new candidates for generalization test.")
        
        conn = init_cache(CACHE_DB)
        audited_df = audit_simbad_labels(df, conn)
        conn.close()
        
        audited_df.to_csv("crossmatch_audit_new_candidates.csv", index=False)
        
        total = len(audited_df)
        matches = audited_df[audited_df["simbad_status"] == 'Match'].shape[0]
        
        # Pre-calculate dictionaries safely to avoid inline syntax errors
        tier_dist = {str(k): int(v) for k, v in audited_df["label_confidence_tier"].value_counts().items()}
        otype_dist = {str(k): int(v) for k, v in audited_df["simbad_otype_raw"].value_counts().items()}

        audit = {
            "pipeline_version": PIPELINE_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "gaia_file": INPUT_FILE,
            "test_rows": int(total),
            "matches": int(matches),
            "match_rate": float(matches / total) if total > 0 else 0.0,
            "cache_hit_rate": float(audited_df["from_cache"].mean()),
            "tier_distribution": tier_dist,
            "otype_distribution": otype_dist
        }
        
        with open("crossmatch_audit_new_candidates.json", "w") as f:
            json.dump(audit, f, indent=2)
            
        print("\n" + "="*60)
        print(f"GENERALIZATION TEST STATISTICS (N={total})")
        print("="*60)
        print(f"Match Rate:        {audit['match_rate']:.2%} ({matches}/{total})")
        print(f"Cache Hit Rate:    {audit['cache_hit_rate']:.2%}")
        
        print("\nLABEL CONFIDENCE TIER DISTRIBUTION:")
        print(audited_df['label_confidence_tier'].value_counts().to_string())
        print("="*60)
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")