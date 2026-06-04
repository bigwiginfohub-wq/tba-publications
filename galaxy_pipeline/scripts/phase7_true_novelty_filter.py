import pandas as pd
import numpy as np
import time
import logging
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Configure Vizier for SDSS DR16 (Catalog V/154/sdss16)
Vizier.ROW_LIMIT = -1
Vizier.columns = ['RA_ICRS', 'DE_ICRS', 'class', 'zsp'] # class: 1=Star, 2=Galaxy, 3=QSO, 6=Other

def query_sdss(ra, dec, radius_arcsec=1.5):
    """Queries SDSS DR16 to see if the optical survey already knows this object"""
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    try:
        # V/154/sdss16 is SDSS DR16
        result = Vizier.query_region(coord, radius=radius_arcsec * u.arcsec, catalog="V/154/sdss16")
        if result and len(result) > 0:
            tab = result[0]
            obj_class = int(tab['class'][0]) if not np.ma.is_masked(tab['class'][0]) else 0
            redshift = float(tab['zsp'][0]) if not np.ma.is_masked(tab['zsp'][0]) else np.nan
            
            class_map = {1: "Star", 2: "Galaxy", 3: "QSO", 6: "Other"}
            return True, class_map.get(obj_class, "Unknown"), redshift
        return False, None, np.nan
    except Exception as e:
        logging.warning(f"VizieR SDSS query failed: {e}")
        return False, None, np.nan

if __name__ == "__main__":
    print("="*70)
    print("PHASE 7: SURVEY-UNIFIED CROSSMATCH (SDSS DR16)")
    print("Filtering out catalog fragmentation artifacts to find true reconciliation.")
    print("="*70)
    
    # Load the final ranked candidates from Phase 4
    try:
        df = pd.read_csv('phase4_final_ranked_candidates.csv')
    except FileNotFoundError:
        logging.error("phase4_final_ranked_candidates.csv not found. Please ensure Phase 4 was run.")
        exit()
    
    logging.info(f"Querying SDSS DR16 for {len(df)} final candidates...")
    
    sdss_found, sdss_class, sdss_z = [], [], []
    
    for idx, row in df.iterrows():
        found, obj_class, redshift = query_sdss(row['ra'], row['dec'])
        sdss_found.append(found)
        sdss_class.append(obj_class)
        sdss_z.append(redshift)
        time.sleep(0.5) # Polite rate limiting for VizieR
        
    df['sdss_found'] = sdss_found
    df['sdss_class'] = sdss_class
    df['sdss_redshift'] = sdss_z
    
    # The Reconciliation: Found in SDSS vs Unmatched (Footprint/Depth limits)
    reconciled = df[df['sdss_found'] == True]
    unmatched = df[df['sdss_found'] == False]
    
    print(f"\n--- RECONCILIATION RESULTS ---")
    print(f"Already known to SDSS (Cross-Survey Confirmed): {len(reconciled)}")
    print(f"SDSS-Unmatched (Outside footprint/depth limits): {len(unmatched)}")
    
    if len(reconciled) > 0:
        print("\n✅ RECONCILED (Known Quasars/Galaxies missed by SIMBAD/NED):")
        print(reconciled[['source_id', 'w1_w2_color', 'sdss_class', 'sdss_redshift']].to_string(index=False))
        
    if len(unmatched) > 0:
        print("\n🔭 SDSS-UNMATCHED (Catalog non-reconciled Gaia objects):")
        print(unmatched[['source_id', 'bp_rp', 'w1_w2_color', 'candidate_score']].to_string(index=False))
        print("\nNote: These are not necessarily 'novelties'. They are likely outside")
        print("the SDSS DR16 footprint, below the magnitude limit, or in crowded fields.")
    else:
        print("\n(All candidates were successfully reconciled with SDSS.)")
        
    df.to_csv('phase7_final_reconciliation.csv', index=False)
    logging.info("Saved final reconciliation to phase7_final_reconciliation.csv")
    print("="*70)