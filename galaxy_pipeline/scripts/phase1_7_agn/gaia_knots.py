from astroquery.gaia import Gaia

query = """
SELECT source_id, ra, dec, phot_g_mean_mag, classprob_dsc_combmod_galaxy, classprob_dsc_combmod_star
FROM gaiadr3.gaia_source
WHERE CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', 204.992453, 0.834006, 0.0015)
) = 1
"""
print("Querying Gaia for nearby knots (5.4 arcsec radius)...\n")
job = Gaia.launch_job(query)
res = job.get_results()

if len(res) <= 1:
    print("✅ Only 1 Gaia source detected in region (isolated nucleus).")
else:
    print(f"⚠️ Found {len(res)} Gaia sources in region (possible multi-knot/merger):")
    print(res)