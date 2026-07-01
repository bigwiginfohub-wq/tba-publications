from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print("🔍 Querying Public Photo-Z Catalogs (5\" radius)...\n")

# Reliable photo-z catalogs on VizieR
catalogs = [
    ("II/364/dr10", "Legacy Survey DR10"),   # phot_z
    ("VII/292/sdss16", "SDSS DR16"),          # photoz
    ("J/ApJ/908/175", "DES DR2"),             # Z_PHOT
    ("V/154/dr8", "LAMOST DR8")               # photoz (spectro-photometric)
]

found = False
for cat_id, cat_name in catalogs:
    try:
        viz = Vizier(columns=["RAJ2000", "DEJ2000", "Source", "phot_z", "photoz", "Z_PHOT", "e_photoz", "err_Z_PHOT"], row_limit=3)
        res = viz.query_region(coord, radius="5s", catalog=[cat_id])
        if res and len(res[cat_id]) > 0:
            print(f"✅ {cat_name} MATCH:")
            tbl = res[cat_id]
            # Find whichever photo-z column exists
            z_col = next((c for c in tbl.colnames if 'photo' in c.lower() or 'z_phot' in c.lower()), None)
            err_col = next((c for c in tbl.colnames if 'err' in c.lower() or 'e_' in c.lower()), None)
            
            if z_col:
                z_val = tbl[z_col][0]
                z_err = tbl[err_col][0] if err_col else "N/A"
                print(f"   z_phot = {z_val:.4f} ± {z_err}")
                found = True
            else:
                print(f"   ⚠️ Catalog returned data but no photo-z column found.")
    except Exception as e:
        print(f"️ {cat_name}: {str(e)[:40]}")

if not found:
    print("\n📭 No public photo-z estimate within 5\".")
    print("   → Common for G≈20.9 compact/blue systems below survey depth limits.")
    print("   → Use web estimator as fallback: https://apoplex.strw.leidenuniv.nl/")

print("\n📊 INTERPRETATION GUIDE:")
print("  z < 0.05  → Nearby dwarf / local volume")
print("  0.05–0.25 → Typical BCD / star-forming compact galaxy")
print("  0.25–0.6  → Moderate-z compact system")
print("  > 0.6     → Distant AGN host / high-z galaxy")