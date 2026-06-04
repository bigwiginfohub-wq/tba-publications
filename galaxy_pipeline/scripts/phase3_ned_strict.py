import pandas as pd
import time
import logging
from astroquery.ipac.ned import Ned
from astropy.coordinates import SkyCoord
import astropy.units as u

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def query_ned(ra, dec, radius_arcsec=1.0): # STRICT 1.0" RADIUS
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    try:
        result = Ned.query_region(coord, radius=radius_arcsec * u.arcsec)
        if result is not None and len(result) > 0:
            obj_type = str(result['Type'][0]) if 'Type' in result.colnames else 'Unknown'
            obj_name = str(result['Object Name'][0]) if 'Object Name' in result.colnames else 'Unnamed'
            return True, obj_type, obj_name
        return False, None, None
    except Exception:
        return False, None, None

if __name__ == "__main__":
    print("="*60)
    print("PHASE 3: STRICT NED VERIFICATION (1.0 arcsec)")
    print("="*60)
    
    df = pd.read_csv('crossmatch_audit_new_candidates.csv')
    unknowns = df[df['label_confidence_tier'] == 'Tier_0_Unknown'].copy()
    
    logging.info(f"Querying NED for {len(unknowns)} SIMBAD-Unknown candidates (1.0\" radius)...")
    
    ned_found, ned_type, ned_name = [], [], []

    for idx, row in unknowns.iterrows():
        found, obj_type, obj_name = query_ned(row['ra'], row['dec'])
        ned_found.append(found)
        ned_type.append(obj_type)
        ned_name.append(obj_name)
        time.sleep(1.0) # Strict rate limiting

    unknowns['ned_found'] = ned_found
    unknowns['ned_type'] = ned_type
    unknowns['ned_name'] = ned_name

    found_df = unknowns[unknowns['ned_found'] == True]
    
    print(f"\n--- RESULTS ---")
    print(f"NED matched {len(found_df)} out of {len(unknowns)} unknowns (at 1.0\").")
    
    if len(found_df) > 0:
        print("\n✅ INDEPENDENT CONFIRMATION FOUND:")
        print(found_df[['source_id', 'bp_rp', 'parallax', 'ned_type', 'ned_name']].to_string(index=False))
    else:
        print("\n🔭 NO NED MATCHES FOUND AT 1.0\".")
        print("These objects are absent from both SIMBAD and NED at strict radii.")
        
    unknowns.to_csv('phase3_ned_strict.csv', index=False)
    print("="*60)