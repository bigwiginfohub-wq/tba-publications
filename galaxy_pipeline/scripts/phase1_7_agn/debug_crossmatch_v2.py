import pandas as pd
from astroquery.simbad import Simbad
from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Load just the first 5 rows to test
df = pd.read_csv('galaxy_candidates.csv').head(5)
logging.info(f"Testing external crossmatch on first {len(df)} sources...")

for idx, row in df.iterrows():
    ra = row['ra']
    dec = row['dec']
    source_id = row['source_id']
    print(f"\n{'='*50}")
    print(f"Source ID: {source_id} | RA: {ra:.4f} | DEC: {dec:.4f}")
    
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    
    # 1. Query SIMBAD (with safe column checking)
    try:
        logging.info("Querying SIMBAD...")
        simbad_result = Simbad.query_region(coord, radius=1.0*u.arcsec)
        if simbad_result is not None and len(simbad_result) > 0:
            if 'OTYPE' in simbad_result.colnames:
                print(f"  ✅ SIMBAD MATCH: {simbad_result['OTYPE'][0]}")
            else:
                print(f"  ✅ SIMBAD MATCH (No OTYPE column). Columns available: {simbad_result.colnames}")
        else:
            print("  ❌ SIMBAD: No match found within 1 arcsec.")
    except Exception as e:
        print(f"  ⚠️ SIMBAD ERROR: {e}")
        
    # 2. Query SDSS using DIRECT SQL (bypasses astroquery field-name bugs)
    try:
        logging.info("Querying SDSS via SQL...")
        # Direct SQL is much more reliable than query_region with photoobj_fields
        sql_query = f"""
        SELECT TOP 1 class, objid, ra, dec 
        FROM PhotoObjAll 
        WHERE CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra}, {dec}, 1.0/3600.0)) = 1
        """
        sdss_result = SDSS.query_sql(sql_query)
        
        if sdss_result is not None and len(sdss_result) > 0:
            print(f"  ✅ SDSS MATCH: Class = {sdss_result['class'][0]} (ObjID: {sdss_result['objid'][0]})")
        else:
            print("  ❌ SDSS: No match found within 1 arcsec.")
    except Exception as e:
        print(f"  ⚠️ SDSS ERROR: {e}")
        
    import time
    time.sleep(1.0)

print(f"\n{'='*50}")
print("Debug v2 complete. Review the output above.")