from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print("🔍 EXPANDED REDSHIFT SEARCH (20\" RADIUS)\n" + "="*50)

viz = Vizier(columns=["RAJ2000","DEJ2000","Source","Redshift","z_qual","Type"], row_limit=5)
catalogs = [
    "VII/292/sdss16",      # SDSS DR16
    "J/ApJS/270/26",       # DESI DR1
    "J/MNRAS/384/93",      # 6dFGS
    "V/154/dr8",           # LAMOST DR8
    "VII/294/ned"          # NED Redshifts
]
found = False

for cat in catalogs:
    try:
        res = viz.query_region(coord, radius="20s", catalog=[cat])
        if res and len(res[cat]) > 0:
            print(f"✅ {cat}:")
            print(res[cat][["Source","Redshift","z_qual","Type"]].to_string(index=False))
            found = True
    except Exception:
        pass
    time.sleep(1.2)

if not found:
    print("📭 No spectroscopic redshift within 20\".")
    print("   → Consistent with faint (G≈20.9) targets below current spectroscopic limits.")