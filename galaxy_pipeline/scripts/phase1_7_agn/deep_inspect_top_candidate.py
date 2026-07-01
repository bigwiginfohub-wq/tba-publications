from astroquery.ipac.ned import Ned
from astroquery.gaia import Gaia
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

coord = SkyCoord(ra=257.312761*u.deg, dec=28.446286*u.deg)
print(f"🔍 DEEP INSPECTION: 4575090461821845504 | RA={coord.ra.deg:.4f} DEC={coord.dec.deg:.4f}\n" + "="*60)

# 1. NED Multi-Radius Cone Search
print("\n📡 NED CONE SEARCH:")
for rad in [5, 10, 20]:
    try:
        res = Ned.query_region(coord, radius=rad*u.arcsec)
        if res is not None and len(res) > 0:
            print(f"  {rad}\": {len(res)} match(es)")
            for i in range(min(2, len(res))):
                print(f"       {res['Object Name'][i]} | {res['Object Type'][i]}")
        else:
            print(f"  {rad}\": NONE")
    except Exception:
        print(f"  {rad}\": TIMEOUT")
    time.sleep(2)

# 2. Gaia 10" Neighborhood
print("\n🌌 GAIA 10\" NEIGHBORHOOD:")
query = f"""
SELECT source_id, ra, dec, phot_g_mean_mag, classprob_dsc_combmod_galaxy, classprob_dsc_combmod_star
FROM gaiadr3.gaia_source
WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {coord.ra.deg}, {coord.dec.deg}, {10.0/3600.0})) = 1
"""
try:
    job = Gaia.launch_job(query)
    gaia_neighbors = job.get_results()
    print(f"  Sources within 10\": {len(gaia_neighbors)}")
    if len(gaia_neighbors) > 1:
        print("  ⚠️ Multiple Gaia detections (possible knot/blend):")
        print(gaia_neighbors)
    else:
        print("  ✅ Isolated Gaia source")
except Exception as e:
    print(f"  ⚠️ Gaia query failed: {e}")

# 3. Legacy Survey DR10 Catalog Check (via Vizier)
print("\n📖 LEGACY SURVEY DR10 CATALOG CHECK:")
try:
    viz = Vizier(columns=["ls_id", "type", "ebv", "decam_g", "decam_r", "decam_z"])
    res = viz.query_region(coord, radius="10s", catalog=["VI/252/ls-dr10"])
    if res and len(res) > 0:
        print("  ✅ Matched in LS DR10:")
        print(res[0])
    else:
        print("  ⚠️ No LS DR10 match within 10\"")
except Exception:
    print("  ️ Vizier query timeout (use viewer links below)")

# 4. Direct Viewer Links
print("\n🔗 DIRECT VIEWER LINKS (Pre-centered):")
print(f"  Legacy Survey DR10: https://legacysurvey.org/viewer?ra={coord.ra.deg}&dec={coord.dec.deg}&layer=ls-dr10&pixscale=0.262&bands=grz")
print(f"  Pan-STARRS DR2:     https://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos={coord.ra.deg}+{coord.dec.deg}&radius=15&width=4&height=4&color=color&imageType=stack&size=600")