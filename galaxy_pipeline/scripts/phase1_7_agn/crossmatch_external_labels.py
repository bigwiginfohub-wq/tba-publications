import pandas as pd
import time
from astroquery.simbad import Simbad
from astroquery.sdss import SDSS
import logging

# Configure logging to see progress
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Configure Simbad to return the object type (otype)
Simbad.add_votable_fields('otype')

def get_external_labels(df):
    logging.info(f"Starting external crossmatch for {len(df)} sources...")
    
    # New columns to hold our independent ground truth
    df['simbad_otype'] = None
    df['sdss_class'] = None
    df['label_confidence'] = 'Unlabeled'
    
    for idx, row in df.iterrows():
        ra = row['ra']
        dec = row['dec']
        
        # 1. Query SIMBAD (1 arcsecond radius)
        try:
            simbad_result = Simbad.query_region(f"J{ra/15:.6f} {dec:.6f}", radius=1/3600) # 1 arcsec in degrees
            if simbad_result is not None:
                df.at[idx, 'simbad_otype'] = simbad_result['OTYPE'][0]
        except Exception as e:
            pass # Silently fail and move on if SIMBAD is busy
            
        # 2. Query SDSS (1 arcsecond radius)
        try:
            sdss_result = SDSS.query_region(f"J{ra/15:.6f} {dec:.6f}", radius=1/3600, photoobj_fields=['class'])
            if sdss_result is not None:
                df.at[idx, 'sdss_class'] = sdss_result['class'][0]
        except Exception as e:
            pass

        # 3. Apply Label Architecture Logic (Conflict Resolution)
        sdss_val = str(df.at[idx, 'sdss_class']).upper() if pd.notna(df.at[idx, 'sdss_class']) else ""
        simbad_val = str(df.at[idx, 'simbad_otype']).upper() if pd.notna(df.at[idx, 'simbad_otype']) else ""
        
        if 'GALAXY' in sdss_val or 'QSO' in sdss_val:
            df.at[idx, 'label_confidence'] = 'High (SDSS)'
        elif 'GALAXY' in simbad_val or 'QSO' in simbad_val or 'AGN' in simbad_val:
            df.at[idx, 'label_confidence'] = 'Medium (SIMBAD)'
        elif 'STAR' in sdss_val or 'STAR' in simbad_val:
            df.at[idx, 'label_confidence'] = 'High_Star'
        else:
            df.at[idx, 'label_confidence'] = 'Unlabeled'

        # Progress update every 50 rows
        if (idx + 1) % 50 == 0:
            logging.info(f"Processed {idx + 1}/{len(df)} sources...")
            
        # Be polite to the servers (avoid rate limiting)
        time.sleep(0.5)

    return df

if __name__ == "__main__":
    try:
        # Load the 500 candidates
        df = pd.read_csv('galaxy_candidates.csv')
        logging.info("Loaded galaxy_candidates.csv")
        
        # Run the crossmatch
        labeled_df = get_external_labels(df)
        
        # Save the new, scientifically valid dataset
        output_file = 'galaxy_candidates_WITH_EXTERNAL_LABELS.csv'
        labeled_df.to_csv(output_file, index=False)
        logging.info(f"✅ SUCCESS! Saved to {output_file}")
        
        # Print a quick summary
        print("\n--- LABEL DISTRIBUTION ---")
        print(labeled_df['label_confidence'].value_counts())
        
    except FileNotFoundError:
        logging.error("Could not find 'galaxy_candidates.csv'. Please ensure it is in the same folder.")