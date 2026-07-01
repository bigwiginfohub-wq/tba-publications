from astroquery.gaia import Gaia

source_id = 4575090461821845504

query = f"""
SELECT
    source_id,
    parallax,
    parallax_error,
    pmra,
    pmdec,
    phot_g_mean_mag,
    bp_rp,
    astrometric_excess_noise,
    ruwe
FROM gaiadr3.gaia_source
WHERE source_id = {source_id}
"""

print("🔍 Querying Gaia DR3 for astrometric parameters...\n")
try:
    job = Gaia.launch_job(query)
    res = job.get_results()
    if len(res) > 0:
        for col in res.colnames:
            print(f"{col:30s} = {res[col][0]}")
    else:
        print("️ No data returned. Verify source_id.")
except Exception as e:
    print(f"❌ Gaia API error: {e}")