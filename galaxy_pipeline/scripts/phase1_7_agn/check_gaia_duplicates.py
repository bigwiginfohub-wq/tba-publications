from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

ra, dec = 257.312761, 28.446286
target = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
radius_deg = 0.0003  # ~1.08 arcseconds

query = f"""
SELECT
    source_id, ra, dec, phot_g_mean_mag,
    classprob_dsc_combmod_star,
    classprob_dsc_combmod_galaxy,
    classprob_dsc_combmod_quasar
FROM gaiadr3.gaia_source
WHERE CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
) = 1
"""

print("🔍 Querying Gaia DR3 within ~1.1\" of target...\n")
for attempt in range(3):
    try:
        job = Gaia.launch_job(query)
        res = job.get_results()
        if len(res) > 0:
            break
        print(f"  Attempt {attempt+1}: Empty. Retrying...")
        time.sleep(5)
    except Exception as e:
        print(f"  Attempt {attempt+1}: {e}. Retrying...")
        time.sleep(5)
else:
    print("❌ Failed after 3 attempts.")
    exit()

print(f"✅ Found {len(res)} source(s) within ~1.1 arcseconds:\n")
for row in res:
    src_coord = SkyCoord(ra=row['ra']*u.deg, dec=row['dec']*u.deg)
    offset = target.separation(src_coord).arcsec
    
    print(f"Source ID: {row['source_id']}")
    print(f"  RA/Dec:  {row['ra']:.6f}, {row['dec']:.6f}")
    print(f"  Offset:  {offset:.3f} arcsec from target")
    print(f"  G mag:   {row['phot_g_mean_mag']:.3f}")
    print(f"  Star:    {row['classprob_dsc_combmod_star']:.2e}")
    print(f"  Galaxy:  {row['classprob_dsc_combmod_galaxy']:.2e}")
    print(f"  Quasar:  {row['classprob_dsc_combmod_quasar']:.2e}")
    print("-" * 45)