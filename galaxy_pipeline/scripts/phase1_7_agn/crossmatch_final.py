import pandas as pd
import numpy as np
import requests
import urllib.parse
import time
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# 1. Configure SIMBAD to return object type
simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype')

def get_external_labels(df):
    logging.info(f"Starting robust external crossmatch for {len(df)} sources...")
    
    # Initialize new columns
    df['simbad_otype'] = np.nan
    df['sdss_class'] = np.nan
    df['label_confidence'] = 'Unlabeled'
    
    for idx, row in df.iterrows():
        ra = row['ra']
        dec = row['dec']
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        
        # --- SIMBAD QUERY (Proven to work) ---
        try:
            result = simbad_custom.query_region(coord, radius=1.0*u.arcsec)
            if result is not None and len(result) > 0 and 'otype' in result.colnames:
                otype = str(result['otype'][0]).upper()
                df.at[idx, 'simbad_otype'] = otype
                
                # Label Logic based on SIMBAD
                if any(x in otype for x in ['GALAXY', 'AGN', 'QSO', 'GIG', 'BCG']):
                    df.at[idx, 'label_confidence'] = 'High_External_Galaxy'
                elif 'STAR' in otype or 'STAR*' in otype:
                    df.at[idx, 'label_confidence'] = 'High_External_Star'
                else:
                    df.at[idx, 'label_confidence'] = f'Ambiguous_SIMBAD_{otype}'
        except Exception as e:
            pass # Silently move on if SIMBAD hiccups

        # --- SDSS QUERY (With 503 retry logic) ---
        try:
            radius_deg = 1.0 / 3600.0 # 1 arcsecond
            sql_query = f"SELECT TOP 1 class FROM PhotoObjAll WHERE CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra}, {dec}, {radius_deg})) = 1"
            encoded_query = urllib.parse.quote(sql_query)
            url = f"https://skyserver.sdss.org/dr16/en/tools/search/x_sql.aspx?cmd={encoded_query}&format=csv"
            
            headers = {'User-Agent': 'GaiaProject/1.0 (Educational Astrophysics Pipeline)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) > 1:
                    # SDSS class: 3=Galaxy, 6=Star, 4=QSO
                    sdss_class_val = lines[1].strip()
                    df.at[idx, 'sdss_class'] = sdss_val
                    
                    if sdss_class_val == '3' or sdss_class_val == '4':
                        if df.at[idx, 'label_confidence'] == 'Unlabeled':
                            df.at[idx, 'label_confidence'] = 'High_SDSS_Galaxy_QSO'
                    elif sdss_class_val == '6':
                        if df.at[idx, 'label_confidence'] == 'Unlabeled':
                            df.at[idx, 'label_confidence'] = 'High_SDSS_Star'
            elif response.status_code == 503:
                df.at[idx, 'sdss_class'] = 'Server_Unavailable'
                
        except Exception as e:
            df.at[idx, 'sdss_class'] = 'Query_Failed'

        # Progress update
        if (idx + 1) % 50 == 0:
            logging.info(f"Processed {idx + 1}/{len(df)} sources...")
            
        # Be polite to servers
        time.sleep(0.5)

    return df

if __name__ == "__main__":
    try:
        logging.info("Loading galaxy_candidates.csv...")
        df = pd.read_csv('galaxy_candidates.csv')
        
        logging.info("Running crossmatch...")
        labeled_df = get_external_labels(df)
        
        output_file = 'galaxy_candidates_LABELED.csv'
        labeled_df.to_csv(output_file, index=False)
        logging.info(f"✅ SUCCESS! Saved to {output_file}")
        
        print("\n" + "="*50)
        print("FINAL LABEL DISTRIBUTION:")
        print(labeled_df['label_confidence'].value_counts())
        print("="*50)
        
    except FileNotFoundError:
        logging.error("Could not find 'galaxy_candidates.csv'.")