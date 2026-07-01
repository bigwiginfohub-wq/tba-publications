import pandas as pd
import numpy as np
import requests
import urllib.parse
import time
import json
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

# 1. Configure SIMBAD to return object type AND main_id
simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype', 'main_id')

def observe_external_labels(df):
    logging.info(f"Starting OBSERVATIONAL crossmatch for {len(df)} sources...")
    
    # Initialize raw observation columns (Item 4: Separate status fields)
    df['simbad_main_id'] = np.nan
    df['simbad_otype_raw'] = np.nan
    df['simbad_status'] = 'Pending'
    
    df['sdss_class_raw'] = np.nan
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
            else:
                df.at[idx, 'simbad_status'] = 'NoMatch'
        except Exception as e:
            logging.warning(f"Row {idx}: SIMBAD Exception -> {e}")
            df.at[idx, 'simbad_status'] = 'Error'

        # --- SDSS OBSERVATION ---
        try:
            radius_deg = SDSS_RADIUS_ARCSEC / 3600.0
            # Request objid to ensure consistent CSV column structure even if class is null
            sql_query = f"SELECT TOP 1 objid, class FROM PhotoObjAll WHERE CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra}, {dec}, {radius_deg})) = 1"
            encoded_query = urllib.parse.quote(sql_query)
            url = f"https://skyserver.sdss.org/dr16/en/tools/search/x_sql.aspx?cmd={encoded_query}&format=csv"
            
            headers = {'User-Agent': 'GaiaProject/1.0 (Educational Astrophysics Pipeline)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                
                # Debug: Print raw response for the first successful SDSS query
                if not first_sdss_printed:
                    logging.info(f"--- RAW SDSS RESPONSE (Row {idx}) ---\n{response.text}\n----------------------------------")
                    first_sdss_printed = True

                if len(lines) > 1:
                    # Parse CSV safely
                    parts = lines[1].split(',')
                    if len(parts) >= 2:
                        df.at[idx, 'sdss_class_raw'] = parts[1].strip()
                        df.at[idx, 'sdss_status'] = 'Match'
                    else:
                        df.at[idx, 'sdss_status'] = 'MalformedResponse'
                else:
                    df.at[idx, 'sdss_status'] = 'NoMatch'
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
        logging.info("Loading galaxy_candidates.csv...")
        full_df = pd.read_csv('galaxy_candidates.csv')
        
        # OBSERVATION MODE: Restrict to TEST_ROWS
        df = full_df.head(TEST_ROWS).copy()
        logging.info(f"Restricted to first {len(df)} rows for observation.")
        
        logging.info("Running observational crossmatch...")
        observed_df = observe_external_labels(df)
        
        # --- ITEM 1: Save Results ---
        output_csv = "crossmatch_observation_results.csv"
        observed_df.to_csv(output_csv, index=False)
        logging.info(f"Saved observation results to {output_csv}")
        
        # --- ITEM 2: Run Manifest ---
        manifest = {
            "run_mode": "observation",
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "input_file": "galaxy_candidates.csv",
            "rows_tested": len(df),
            "simbad_radius_arcsec": SIMBAD_RADIUS_ARCSEC,
            "sdss_radius_arcsec": SDSS_RADIUS_ARCSEC,
            "version": "observation_v2"
        }
        with open("crossmatch_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        logging.info("Saved run manifest to crossmatch_manifest.json")
        
        # --- ITEM 3: Query Coverage Statistics ---
        total = len(observed_df)
        simbad_matches = observed_df[observed_df["simbad_status"] == 'Match'].shape[0]
        sdss_matches = observed_df[observed_df["sdss_status"] == 'Match'].shape[0]
        
        print("\n" + "="*60)
        print("COVERAGE STATISTICS:")
        print("="*60)
        print(f"Total Rows Tested: {total}")
        print(f"SIMBAD Match Rate: {simbad_matches/total:.2%} ({simbad_matches}/{total})")
        print(f"SDSS Match Rate:   {sdss_matches/total:.2%} ({sdss_matches}/{total})")
        
        print("\n" + "="*60)
        print("UNIQUE SIMBAD OTYPEs FOUND:")
        print("="*60)
        unique_otypes = observed_df['simbad_otype_raw'].dropna().unique()
        if len(unique_otypes) > 0:
            for otype in unique_otypes:
                count = (observed_df['simbad_otype_raw'] == otype).sum()
                print(f"  '{otype}' : {count} occurrence(s)")
        else:
            print("  (None found in this sample)")
            
        print("\n" + "="*60)
        print("MANUAL INSPECTION TABLE (First 10):")
        print("="*60)
        cols_to_show = ['source_id', 'simbad_main_id', 'simbad_otype_raw', 'simbad_status', 'sdss_class_raw', 'sdss_status']
        print(observed_df[cols_to_show].head(10).to_string(index=False))
        print("="*60)
        
    except FileNotFoundError:
        logging.error("Could not find 'galaxy_candidates.csv'.")