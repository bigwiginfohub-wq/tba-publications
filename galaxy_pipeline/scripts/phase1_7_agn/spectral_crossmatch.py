from astroquery.sdss import SDSS
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print("🔍 SPECTROSCOPIC CROSS-MATCH (10\" RADIUS)\n" + "="*50)

# 1. SDSS DR16 SpecObj
print("\n📡 SDSS DR16 Spectra:")
try:
    sdss = SDSS.query_region(
        coord, 
        radius=10*u.arcsec, 
        data_release=16, 
        spectro=True,
        specobj_fields=['objid','ra','dec','specclass','z','zwarning','plate','mjd','fiberid']
    )
    if sdss is not None and len(sdss) > 0:
        print("✅ MATCH FOUND:")
        print(sdss[["objid","specclass","z","zwarning"]].to_string(index=False))
    else:
        print("  No SDSS spectra within 10\"")
except Exception as e:
    print(f"  ⚠️ SDSS query failed: {str(e)[:40]}")

time.sleep(2)

# 2. DESI DR1 & EDR Spectra (via Vizier)
print("\n📡 DESI Spectra (DR1 + EDR):")
desi_cats = ["J/ApJS/270/26", "J/ApJS/267/15"]  # DR1, EDR
viz = Vizier(columns=["TargetID","RA","DEC","Spectype","Z","ZWARN"], row_limit=5)
found_desi = False

for cat in desi_cats:
    try:
        res = viz.query_region(coord, radius="10s", catalog=[cat])
        if res and len(res[cat]) > 0:
            print(f"✅ MATCH FOUND in {cat}:")
            print(res[cat][["TargetID","Spectype","Z","ZWARN"]].to_string(index=False))
            found_desi = True
            break
    except Exception as e:
        print(f"  ⚠️ {cat} query skipped: {str(e)[:40]}")
    time.sleep(1.5)

if not found_desi:
    print("  No DESI spectra within 10\"")

print("\n" + "="*50)
print(" INTERPRETATION GUIDE:")
print("  specclass/Spectype = GALAXY/QSO/STAR")
print("  z/Z > 0.01 → Extragalactic")
print("  zwarning/ZWARN = 0 → Reliable redshift")