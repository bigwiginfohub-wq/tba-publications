from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print("🔍 CHECKING HIGH-ENERGY ARCHIVES (X-RAY)\n" + "="*50)

# 1. ROSAT All-Sky (Faint Source Catalog) - Good for all-sky coverage
try:
    viz = Vizier(columns=["RAJ2000", "DEJ2000", "Name", "e_count_rate"], row_limit=5)
    # RASS BSC (Bright) and FSC (Faint)
    res = viz.query_region(coord, radius="30s", catalog=["IX/37/rassbsc", "IX/37/rassfsc"])
    if res:
        for k, v in res.items():
            if len(v) > 0:
                print(f"✅ ROSAT DETECTION in {k}:")
                print(v[["Name", "RAJ2000", "DEJ2000"]].to_string(index=False))
            else:
                print(f"   ⚠️ No ROSAT match in {k}")
    else:
        print("📭 No ROSAT detection.")
except Exception as e:
    print(f"   ROSAT Query Failed: {e}")

# 2. Chandra / XMM Pointed Observations
try:
    viz = Vizier(columns=["RAJ2000", "DEJ2000", "ObsID", "Target"], row_limit=5)
    # Chandra Source Catalog
    res_cxc = viz.query_region(coord, radius="30s", catalog=["IX/144/csc2"])
    if res_cxc and len(res_cxc) > 0:
        print("\n✅ CHANDRA DETECTION:")
        print(res_cxc[0][["ObsID", "Target", "RAJ2000", "DEJ2000"]].to_string(index=False))
    else:
        print("\n📭 No Chandra detection.")
except Exception as e:
    print(f"   Chandra Query Failed: {e}")

print("\n" + "="*50)
print(" INTERPRETATION:")
print("  • DETECTION → High confidence AGN / Accreting Black Hole.")
print("  • NO DETECTION → Likely Compact Starburst / Blue Compact Dwarf.")