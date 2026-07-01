import requests
import pandas as pd
import io
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print("🔍 2-ARCSECOND CROSS-MATCH\n" + "="*50)

# Pan-STARRS DR2
ps1_url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
ps1_params = {"ra": coord.ra.deg, "dec": coord.dec.deg, "radius": 2/3600, "nDetections.gt": 1}
r = requests.get(ps1_url, params=ps1_params)
if r.ok and r.text.strip():
    ps1 = pd.read_csv(io.StringIO(r.text))
    print(f"Pan-STARRS matches within 2\": {len(ps1)}")
    if len(ps1) > 0:
        print(ps1.iloc[0])  # Safely prints all available columns for the match
else:
    print("Pan-STARRS: No match within 2\"")

# Legacy Survey DR10
viz = Vizier(columns=["ls_id", "type", "decam_g", "decam_r", "decam_z"])
try:
    ls = viz.query_region(coord, radius="2s", catalog=["VI/252/ls-dr10"])
    if ls and len(ls) > 0:
        print("\nLegacy Survey DR10 match:")
        print(ls[0])
    else:
        print("\nLegacy Survey DR10: No match within 2\"")
except Exception as e:
    print(f"\nLegacy Survey DR10: Query failed ({e})")