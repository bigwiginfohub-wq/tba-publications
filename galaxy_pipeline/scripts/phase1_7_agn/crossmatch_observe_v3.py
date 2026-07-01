import pandas as pd
import numpy as np
import requests
import urllib.parse
import time
import json
import csv
from io import StringIO
from datetime import datetime
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- CONFIGURATION ---
SIMBAD_RADIUS_ARCSEC = 1.0
SDSS_RADIUS_ARCSEC = 1.0
TEST_ROWS = 20
INPUT_FILE = "gaia_phase1_sample.csv"

# 1. Configure SIMBAD: Only request 'otype' explicitly. 'main_id', 'ra', 'dec' are default.
simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype')

def observe_external_labels(df):
    logging.info(f"Starting OBSERVATIONAL crossmatch for {len(df)} sources...")
    
    # Initialize columns safely with None to avoid float/string mixing warnings
    df['simbad_main_id'] = None
    df['simbad_otype_raw'] = None
    df['simbad_sep_arcsec'] = None
    df['simbad_status'] = 'Pending'
    
    df['sdss_class_raw'] = None
    df['sdss_status'] = 'Pending'
    
    first_sdss_printed = False

    for idx, row in df.iterrows():
        ra = row['ra']
        dec = row['dec']
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        
        # --- SIMBAD OBSERVATION ---
        try:
            result = simbad_custom.query_region(coord, radius=SIMBAD_RADIUS_ARCSEC*u.arcsec)
            if result is not None and len(result) > 0:
                df.at[idx, 'simbad_status'] = 'Match'
                
                if 'main_id' in result.colnames:
                    df.at[idx, 'simbad_main_id'] = str(result['main_id'][0]).strip()
                if 'otype' in result.colnames:
                    df.at[idx, 'simbad_otype_raw'] = str(result['otype'][0]).strip()
                    
                # Calculate angular separation
                try:
                    # SIMBAD ra/dec are typically in degrees in the VOTable
                    matched_coord = SkyCoord(ra=result['ra'][0]*u.deg, dec=result['dec'][0]*u.deg)
                    sep = coord.separation(matched_coord)
                    df.at[idx, 'simbad_sep_arcsec'] = round(sep.arcsec, 4)
                except Exception as sep_err:
                    logging.warning(f"Row {idx}: Separation calc failed: {sep_err}")
            else:
                df.at[idx, 'simbad_status'] = 'NoMatch'
        except Exception as e:
            logging.warning(f"Row {idx}: SIMBAD Exception -> {e}")
            df.at[idx, 'simbad_status'] = 'Error'

        # --- SDSS OBSERVATION ---
        try:
            radius_deg = SDSS_RADIUS_ARCSEC / 3600.0
            sql_query = f"SELECT TOP 1 objid, class FROM PhotoObjAll WHERE CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra}, {dec}, {radius_deg})) = 1"
            encoded_query = urllib.parse.quote(sql_query)
            url = f"https://skyserver.sdss.org/dr16/en/tools/search/x_sql.aspx?cmd={encoded_query}&format=csv"
            
            headers = {'User-Agent': 'GaiaProject/1.0 (Educational Astrophysics Pipeline)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            # Debug: Print raw response snippet for the first query
            if not first_sdss_printed:
                logging.info(f"--- RAW SDSS RESPONSE SNIPPET (Row {idx}) ---\n{response.text[:300]}\n----------------------------------")
                first_sdss_printed = True

            if response.status_code == 200:
                # Robust CSV parsing
                try:
                    reader = csv.reader(StringIO(response.text))
                    rows = list(reader)
                    if len(rows) >= 2:
                        # rows[0] is header, rows[1] is data
                        data_row = rows[1]
                        if len(data_row) >= 2:
                            df.at[idx, 'sdss_class_raw'] = data_row[1].strip()
                            df.at[idx, 'sdss_status'] = 'Match'
                        else:
                            df.at[idx, 'sdss_status'] = 'MalformedResponse'
                    else:
                        df.at[idx, 'sdss_status'] = 'NoMatch'
                except Exception as csv_err:
                    logging.warning(f"Row {idx}: CSV parsing failed: {csv_err}")
                    df.at[idx, 'sdss_status'] = 'ParseError'
            elif response.status_code == 503:
                df.at[idx, 'sdss_status'] = 'Server_Unavailable'
            else:
                df.at[idx, 'sdss_status'] = f'HTTP_{response.status_code}'
                
        except Exception as e:
            logging.warning(f"Row {idx}: SDSS Exception -> {e}")
            df.at[idx, 'sdss_status'] = 'Error'

        # Be polite to servers
        time.sleep(0.5)

    return df

if __name__ == "__main__":
    try:
        logging.info(f"Loading {INPUT_FILE}...")
        full_df = pd.read_csv(INPUT_FILE)
        
        # OBSERVATION MODE: Restrict to TEST_ROWS
        df = full_df.head(TEST_ROWS).copy()
        logging.info(f"Restricted to first {len(df)} rows for observation.")
        
        logging.info("Running observational crossmatch...")
        observed_df = observe_external_labels(df)
        
        # --- SAVE RESULTS ---
        output_csv = "crossmatch_observation_results.csv"
        observed_df.to_csv(output_csv, index=False)
        logging.info(f"Saved observation results to {output_csv}")
        
        # --- SAVE MANIFEST ---
        manifest = {
            "run_mode": "observation",
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "input_file": INPUT_FILE,
            "rows_tested": len(df),
            "simbad_radius_arcsec": SIMBAD_RADIUS_ARCSEC,
            "sdss_radius_arcsec": SDSS_RADIUS_ARCSEC,
            "version": "observation_v3"
        }
        with open("crossmatch_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
            
        # --- SAVE AUDIT JSON ---
        total = len(observed_df)
        simbad_matches = observed_df[observed_df["simbad_status"] == 'Match'].shape[0]
        sdss_matches = observed_df[observed_df["sdss_status"] == 'Match'].shape[0]
        
        unique_otypes = observed_df['simbad_otype_raw'].dropna().unique().tolist()
        
        audit = {
            "rows_tested": int(total),
            "simbad_matches": int(simbad_matches),
            "sdss_matches": int(sdss_matches),
            "simbad_match_rate": float(simbad_matches / total) if total > 0 else 0.0,
            "sdss_match_rate": float(sdss_matches / total) if total > 0 else 0.0,
            "unique_simbad_types": unique_otypes
        }
        with open("crossmatch_audit.json", "w") as f:
            json.dump(audit, f, indent=2)
        logging.info("Saved run manifest and audit JSON files.")
        
        # --- PRINT SUMMARY ---
        print("\n" + "="*60)
        print("COVERAGE STATISTICS:")
        print("="*60)
        print(f"Total Rows Tested: {total}")
        print(f"SIMBAD Match Rate: {audit['simbad_match_rate']:.2%} ({simbad_matches}/{total})")
        print(f"SDSS Match Rate:   {audit['sdss_match_rate']:.2%} ({sdss_matches}/{total})")
        
        print("\n" + "="*60)
        print("UNIQUE SIMBAD OTYPEs FOUND:")
        print("="*60)
        if len(unique_otypes) > 0:
            for otype in unique_otypes:
                count = (observed_df['simbad_otype_raw'] == otype).sum()
                print(f"  '{otype}' : {count} occurrence(s)")
        else:
            print("  (None found in this sample)")
            
        print("\n" + "="*60)
        print("MANUAL INSPECTION TABLE (First 10):")
        print("="*60)
        cols_to_show = ['source_id', 'simbad_main_id', 'simbad_otype_raw', 'simbad_sep_arcsec', 'simbad_status', 'sdss_class_raw', 'sdss_status']
        print(observed_df[cols_to_show].head(10).to_string(index=False))
        print("="*60)
        
    except FileNotFoundError:
        logging.error(f"Could not find '{INPUT_FILE}'. Please ensure it exists.")