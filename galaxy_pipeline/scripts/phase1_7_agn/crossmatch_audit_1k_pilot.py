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

# --- CONFIGURATION ---
SIMBAD_RADIUS_ARCSEC = 1.0
TEST_ROWS = 1000  # <-- CHANGE THIS
INPUT_FILE = "gaia_phase1_scaled_1k.csv" # <-- CHANGE THIS
PIPELINE_VERSION = "crossmatch_audit_1k_pilot" # <-- CHANGE THIS
CACHE_DB = "simbad_cache.db"

# Initialize SIMBAD with timeout protection
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
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cache 
        ON simbad_cache(ra, dec, radius)
    ''')
    conn.commit()
    return conn

def get_cached_result(conn, ra_key, dec_key, radius):
    cursor = conn.cursor()
    cursor.execute("SELECT result_json FROM simbad_cache WHERE ra=? AND dec=? AND radius=?", 
                   (ra_key, dec_key, radius))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return None

def cache_result(conn, ra_key, dec_key, radius, result_dict):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO simbad_cache (ra, dec, radius, result_json) 
        VALUES (?, ?, ?, ?)
    ''', (ra_key, dec_key, radius, json.dumps(result_dict)))

def process_match(df, idx, result_dict, coord):
    """Helper function to process a successful match (cached or fresh)"""
    df.at[idx, 'simbad_status'] = 'Match'
    
    # Provenance: Record how many objects were found in the cone
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
    
    sep = coord.separation(matched_coord)
    sep_arcsec = float(sep.arcsec)
    df.at[idx, 'simbad_sep_arcsec'] = sep_arcsec
    
    if sep_arcsec <= 0.2:
        df.at[idx, 'crossmatch_quality'] = 'Excellent'
    elif sep_arcsec <= 0.5:
        df.at[idx, 'crossmatch_quality'] = 'Good'
    elif sep_arcsec <= 0.8:
        df.at[idx, 'crossmatch_quality'] = 'Review'
    else:
        df.at[idx, 'crossmatch_quality'] = 'LowConfidence'

def audit_simbad_labels(df, conn):
    logging.info(f"Starting SIMBAD audit for {len(df)} sources (final optimized version)...")
    
    df['simbad_main_id'] = None
    df['simbad_otype_raw'] = None
    df['simbad_sep_arcsec'] = None
    df['simbad_match_count'] = 0  # NEW: Provenance tracking
    df['crossmatch_quality'] = None
    df['simbad_status'] = 'Pending'
    df['label_confidence_tier'] = 'Pending'
    df['catalog_source'] = 'SIMBAD'
    df['query_radius_arcsec'] = SIMBAD_RADIUS_ARCSEC
    df['from_cache'] = False

    for idx, row in df.iterrows():
        ra = row['ra']
        dec = row['dec']
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        
        ra_key = round(ra, 6)
        dec_key = round(dec, 6)
        
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
                    # ROBUST JSON SERIALIZATION (Prevents numpy/bytes TypeError)
                    result_dict = {'_length': len(result)}
                    for col in result.colnames:
                        values = []
                        for v in result[col]:
                            if hasattr(v, "item"):
                                v = v.item()
                            values.append(str(v) if isinstance(v, bytes) else v)
                        result_dict[col] = values
                    
                    process_match(df, idx, result_dict, coord)
                else:
                    result_dict = {"_status": "NoMatch", "_length": 0}
                    df.at[idx, 'simbad_status'] = 'NoMatch'
                    df.at[idx, 'label_confidence_tier'] = 'Tier_0_Unknown'
                
                cache_result(conn, ra_key, dec_key, SIMBAD_RADIUS_ARCSEC, result_dict)
                time.sleep(0.2) # Only sleep on network queries
                
            except Exception as e:
                logging.warning(f"Row {idx}: SIMBAD Network Exception -> {e}")
                df.at[idx, 'simbad_status'] = 'Error'
                df.at[idx, 'label_confidence_tier'] = 'Error'

        if (idx + 1) % 100 == 0:
            conn.commit()
            cache_hits = df['from_cache'].sum()
            logging.info(f"Processed {idx+1}/{len(df)} sources... (Cache hits: {cache_hits}, Committed to DB)")
            
    conn.commit()
    return df

if __name__ == "__main__":
    try:
        logging.info(f"Loading {INPUT_FILE}...")
        full_df = pd.read_csv(INPUT_FILE)
        
        required_columns = ["ra", "dec"]
        missing = [c for c in required_columns if c not in full_df.columns]
        if missing:
            raise ValueError(f"Missing required columns in {INPUT_FILE}: {missing}")
            
        df = full_df.head(TEST_ROWS).copy()
        logging.info(f"Restricted to first {len(df)} rows for audit.")
        
        logging.info("Initializing optimized SQLite cache...")
        conn = init_cache(CACHE_DB)
        
        logging.info("Running SIMBAD audit...")
        audited_df = audit_simbad_labels(df, conn)
        conn.close()
        
        output_csv = f"crossmatch_audit_{TEST_ROWS}_final.csv"
        audited_df.to_csv(output_csv, index=False)
        logging.info(f"Saved audit results to {output_csv}")
        
        total = len(audited_df)
        matches = audited_df[audited_df["simbad_status"] == 'Match'].shape[0]
        
        status_dist = audited_df["simbad_status"].value_counts().to_dict()
        quality_dist = audited_df["crossmatch_quality"].value_counts().to_dict()
        
        audit = {
            "pipeline_version": PIPELINE_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "gaia_file": INPUT_FILE,
            "test_rows": int(total),
            "radius_arcsec": SIMBAD_RADIUS_ARCSEC,
            "matches": int(matches),
            "match_rate": float(matches / total) if total > 0 else 0.0,
            "cache_hit_rate": float(audited_df["from_cache"].mean()),
            "low_confidence_matches": int((audited_df["crossmatch_quality"] == "LowConfidence").sum()),
            "status_distribution": {str(k): int(v) for k, v in status_dist.items()},
            "crossmatch_quality_distribution": {str(k): int(v) for k, v in quality_dist.items()},
            "tier_distribution": {str(k): int(v) for k, v in audited_df["label_confidence_tier"].value_counts().to_dict().items()},
            "otype_distribution": {str(k): int(v) for k, v in audited_df["simbad_otype_raw"].value_counts().to_dict().items()}
        }
        
        with open(f"crossmatch_audit_{TEST_ROWS}_final.json", "w") as f:
            json.dump(audit, f, indent=2)
        logging.info("Saved audit JSON.")
        
        print("\n" + "="*60)
        print(f"SIMBAD AUDIT STATISTICS (N={total})")
        print("="*60)
        print(f"Match Rate:        {audit['match_rate']:.2%} ({matches}/{total})")
        print(f"Cache Hit Rate:    {audit['cache_hit_rate']:.2%}")
        print(f"Low Confidence:    {audit['low_confidence_matches']} matches")
        
        print("\n" + "="*60)
        print("LABEL CONFIDENCE TIER DISTRIBUTION:")
        print("="*60)
        print(audited_df['label_confidence_tier'].value_counts().to_string())
        
        print("\n" + "="*60)
        print("CONTAMINATION CHECK (Stellar High):")
        print("="*60)
        stellar = audited_df[audited_df['label_confidence_tier'] == 'Tier_1_Stellar_High']
        if len(stellar) > 0:
            print(f"Found {len(stellar)} stellar contaminants.")
            display_df = stellar[['source_id', 'simbad_otype_raw', 'simbad_sep_arcsec', 'simbad_match_count', 'crossmatch_quality']].copy()
            display_df['simbad_sep_arcsec'] = display_df['simbad_sep_arcsec'].round(4)
            print(display_df.head(5).to_string(index=False))
        else:
            print("  (No stellar contaminants found)")
        print("="*60)
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")