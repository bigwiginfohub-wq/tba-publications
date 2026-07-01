import requests
import urllib.parse
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
    result = simbad_custom.query_object("M31")
    if result is not None and len(result) > 0:
        print("✅ SUCCESS! SIMBAD returned data.")
        print(f"   Available Columns: {result.colnames}")
        # Safely get the first row's data without hardcoding column names
        first_row = result[0]
        print(f"   First Row Data: {dict(first_row)}")
    else:
        print("❌ FAILED: No result returned for M31.")
except Exception as e:
    print(f"⚠️ ERROR: {e}")


print("\n" + "="*60)
print("TEST 2: SDSS DIRECT API (Testing on a known SDSS Galaxy)")
print("="*60)

# Known galaxy coordinates (approx)
ra_test = 150.0
dec_test = 2.0
radius_deg = 0.001 # ~3.6 arcseconds

# The SQL query
sql_query = f"SELECT TOP 1 objid, class, ra, dec FROM PhotoObjAll WHERE CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra_test}, {dec_test}, {radius_deg})) = 1"

# URL-encode the query to prevent formatting issues
encoded_query = urllib.parse.quote(sql_query)
url = f"https://skyserver.sdss.org/dr16/en/tools/search/x_sql.aspx?cmd={encoded_query}&format=csv"

# FIX: Add a polite User-Agent header so SDSS doesn't block us as a bot
headers = {
    'User-Agent': 'GaiaProject/1.0 (Educational Astrophysics Pipeline)'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status() # Raise error if HTTP status is not 200
    
    lines = response.text.strip().split('\n')
    if len(lines) > 1:
        print("✅ SUCCESS! SDSS Response:")
        print(f"   Header: {lines[0]}")
        print(f"   Data:   {lines[1]}")
        print("   (Note: In SDSS, class '3' = Galaxy, '6' = Star, '4' = QSO)")
    else:
        print("❌ FAILED: SDSS returned no data for this coordinate.")
        print(f"   Raw response: {response.text}")
except requests.exceptions.HTTPError as e:
    print(f"⚠️ HTTP ERROR: {e}")
    print(f"   Response text: {response.text}")
except Exception as e:
    print(f"⚠️ ERROR: {e}")

print("\n" + "="*60)
print("Plumbing test v2 complete.")
print("="*60)