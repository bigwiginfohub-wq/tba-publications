import requests
from astroquery.simbad import Simbad
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

print("="*60)
print("TEST 1: SIMBAD (Testing on M31 - Andromeda Galaxy)")
print("="*60)

# 1. Create a custom Simbad instance and explicitly request 'otype'
simbad_custom = Simbad()
simbad_custom.add_votable_fields('otype', 'ra', 'dec')

try:
    # Query a known galaxy
    result = simbad_custom.query_object("M31")
    if result is not None and len(result) > 0:
        print(f"✅ SUCCESS! Found: {result['MAIN_ID'][0]}")
        print(f"   Object Type (OTYPE): {result['OTYPE'][0]}")
    else:
        print("❌ FAILED: No result returned for M31.")
except Exception as e:
    print(f"⚠️ ERROR: {e}")


print("\n" + "="*60)
print("TEST 2: SDSS DIRECT API (Testing on a known SDSS Galaxy)")
print("="*60)

# SDSS SkyServer direct URL (bypasses astroquery's broken VOTable parser)
# We will query a known galaxy: RA=150.0, Dec=2.0 (approx)
ra_test = 150.0
dec_test = 2.0
radius_arcsec = 2.0

# Direct HTTP GET request to SDSS SkyServer
url = f"https://skyserver.sdss.org/dr16/en/tools/search/x_sql.aspx?cmd=SELECT+TOP+1+objid,+class,+ra,+dec+FROM+PhotoObjAll+WHERE+CONTAINS(POINT('J2000',+ra,+dec),+CIRCLE('J2000',+{ra_test},+{dec_test},+{radius_arcsec}/3600.0))=1&format=csv"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status() # Raise error if HTTP status is not 200
    
    # SDSS returns CSV. Let's read it.
    lines = response.text.strip().split('\n')
    if len(lines) > 1:
        print(f"✅ SUCCESS! SDSS Response:")
        print(f"   Header: {lines[0]}")
        print(f"   Data:   {lines[1]}")
        # In SDSS, class '3' = Galaxy, '6' = Star, '4' = QSO
    else:
        print("❌ FAILED: SDSS returned no data for this coordinate.")
        print(f"   Raw response: {response.text}")
except Exception as e:
    print(f"⚠️ ERROR: {e}")

print("\n" + "="*60)
print("Plumbing test complete.")
print("="*60)