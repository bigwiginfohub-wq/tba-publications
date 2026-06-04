import pandas as pd
import numpy as np
import time
import logging
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Configure Vizier for AllWISE (Catalog II/328/allwise)
Vizier.ROW_LIMIT = -1
Vizier.columns = ['W1mag', 'W2mag', 'e_W1mag', 'e_W2mag']

def query_allwise(ra, dec, radius_arcsec=1.0):
    """Queries the AllWISE catalog via VizieR"""
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    try:
        result = Vizier.query_region(coord, radius=radius_arcsec * u.arcsec, catalog="II/328/allwise")
        if result and len(result) > 0:
            table = result[0]
            w1 = float(table['W1mag'][0]) if not np.ma.is_masked(table['W1mag'][0]) else np.nan
            w2 = float(table['W2mag'][0]) if not np.ma.is_masked(table['W2mag'][0]) else np.nan
            return True, w1, w2
        return False, np.nan, np.nan
    except Exception as e:
        logging.warning(f"VizieR query failed: {e}")
        return False, np.nan, np.nan

def calculate_candidate_score(row):
    """
    Calculates the TRACEBIND Candidate Score based on the reviewer's criteria.
    Higher score = Stronger Extragalactic/AGN Candidate.
    """
    score = 0.0
    
    # 1. Astrometric Stationarity (Max +3 points)
    if row['parallax_snr'] < 1.0: score += 1.5
    elif row['parallax_snr'] < 2.0: score += 0.5
    
    if row['pm_total'] < 0.5: score += 1.5
    elif row['pm_total'] < 1.0: score += 0.5
    
    # 2. Astrometric Cleanliness (Max +1 point)
    if row['ruwe'] < 1.1: score += 1.0
    elif row['ruwe'] < 1.4: score += 0.5
    
    # 3. Optical Color (Max +1 point)
    if 0.5 <= row['bp_rp'] <= 0.7: score += 1.0
    
    # 4. Infrared AGN Signature (Max +3 points) - THE SMOKING GUN
    if not np.isnan(row['w1_w2_color']):
        if row['w1_w2_color'] > 0.8: score += 3.0  # Classic AGN dust torus
        elif row['w1_w2_color'] > 0.5: score += 1.5
        
    return score

if __name__ == "__main__":
    print("="*60)
    print("PHASE 4: ALLWISE INFRARED CROSSMATCH & CANDIDATE SCORING")
    print("="*60)
    
    # Load the data and isolate the 12 Pure Unknowns
    df = pd.read_csv('crossmatch_audit_new_candidates.csv')
    ned = pd.read_csv('phase3_ned_strict.csv')
    ned_matches = ned[ned['ned_found'] == True]['source_id'].tolist()
    
    pure_unknowns = df[(df['label_confidence_tier'] == 'Tier_0_Unknown') & (~df['source_id'].isin(ned_matches))].copy()
    
    # Calculate physical metrics
    pure_unknowns['parallax_snr'] = np.abs(pure_unknowns['parallax'] / pure_unknowns['parallax_error'])
    pure_unknowns['pm_total'] = np.sqrt(pure_unknowns['pmra']**2 + pure_unknowns['pmdec']**2)
    
    logging.info(f"Querying AllWISE for {len(pure_unknowns)} Pure Unknowns...")
    
    wise_found, w1_mags, w2_mags = [], [], []
    
    for idx, row in pure_unknowns.iterrows():
        found, w1, w2 = query_allwise(row['ra'], row['dec'])
        wise_found.append(found)
        w1_mags.append(w1)
        w2_mags.append(w2)
        time.sleep(0.5) # Polite rate limiting
        
    pure_unknowns['wise_found'] = wise_found
    pure_unknowns['w1_mag'] = w1_mags
    pure_unknowns['w2_mag'] = w2_mags
    pure_unknowns['w1_w2_color'] = pure_unknowns['w1_mag'] - pure_unknowns['w2_mag']
    
    # Calculate the TRACEBIND Score
    pure_unknowns['candidate_score'] = pure_unknowns.apply(calculate_candidate_score, axis=1)
    
    # Sort by score descending
    pure_unknowns = pure_unknowns.sort_values('candidate_score', ascending=False)
    
    print("\n--- FINAL RANKED CANDIDATE LIST ---")
    cols = ['source_id', 'bp_rp', 'parallax_snr', 'pm_total', 'ruwe', 'w1_w2_color', 'candidate_score']
    print(pure_unknowns[cols].to_string(index=False))
    
    print("\n" + "="*60)
    print("SCORING GUIDE (Max 8.0 points):")
    print("> 6.0 : Prime Spectroscopic Target (Strong AGN/Extragalactic signature)")
    print("4.0-6.0: Plausible Candidate (Requires Pan-STARRS morphology check)")
    print("< 4.0 : Weak Candidate (Likely stellar or artifact)")
    print("="*60)
    
    pure_unknowns.to_csv('phase4_final_ranked_candidates.csv', index=False)
    logging.info("Saved final ranked list to phase4_final_ranked_candidates.csv")
