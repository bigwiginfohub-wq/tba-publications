from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print("🔍 SPECTROSCOPIC REDSHIFT & LS MORPHOLOGY CHECK\n" + "="*55)

# ──────────────────────────────────────────────────────────────
# 1. SPECTROSCOPIC REDSHIFT SEARCH (10" radius)
# ─────────────────────────────────────────────────────────────
print("\n📡 SPECTROSCOPIC REDSHIFT CATALOGS:")
viz = Vizier(columns=["RAJ2000", "DEJ2000", "Source", "Redshift", "z_qual", "Type"], row_limit=5)
# SDSS DR16, DESI DR1, 6dFGS, LAMOST DR8, NED Redshifts
catalogs = ["VII/292/sdss16", "J/ApJS/270/26", "J/MNRAS/384/93", "V/154/dr8", "VII/294/ned"]
found_spec = False

for cat in catalogs:
    try:
        res = viz.query_region(coord, radius="10s", catalog=[cat])
        if res and len(res[cat]) > 0:
            print(f"✅ {cat}:")
            print(res[cat][["Source", "Redshift", "z_qual", "Type"]].to_string(index=False))
            found_spec = True
    except Exception:
        pass  # Skip timeouts/rate limits
    time.sleep(1)

if not found_spec:
    print("  📭 No spectroscopic redshift found within 10\".")

# ──────────────────────────────────────────────────────────────
# 2. LEGACY SURVEY DR10 TRACTOR MORPHOLOGY
# ─────────────────────────────────────────────────────────────
print("\n📡 LEGACY SURVEY DR10 MORPHOLOGY:")
try:
    viz_ls = Vizier(columns=["ls_id", "type", "g", "r", "z", "phot_z"], row_limit=3)
    res_ls = viz_ls.query_region(coord, radius="5s", catalog=["II/364/dr10"])
    if res_ls and len(res_ls) > 0:
        print("✅ Tractor Match:")
        print(res_ls[0][["ls_id", "type", "g", "r", "z", "phot_z"]].to_string(index=False))
        
        ls_type = str(res_ls[0]["type"][0]).upper()
        print(f"  👉 TYPE: {ls_type}")
        
        if ls_type in ["EXP", "DEV", "REX", "SER", "COMP"]:
            print("  🟩 Resolved galaxy morphology confirmed")
        elif ls_type == "PSF":
            print("  🔴 Point source (consistent with QSO/AGN nucleus)")
        else:
            print(f"  ⚠️ Unrecognized type: {ls_type}")
    else:
        print("  ⚠️ No LS DR10 Tractor match within 5\".")
except Exception as e:
    print(f"   LS query failed: {str(e)[:40]}")

print("\n" + "="*55)
print("📝 CLASSIFICATION DECISION TREE:")
print("  1. z > 0.01 + TYPE = EXP/DEV/REX → Confirmed Galaxy")
print("  2. z > 0.5 + TYPE = PSF → Quasar / AGN")
print("  3. No spectrum + Blue colors + Extended → Blue Compact Dwarf / Star-forming Galaxy")
print("  4. No spectrum + Point-like + Blue → Faint QSO candidate")