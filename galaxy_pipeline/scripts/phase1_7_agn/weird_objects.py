from astroquery.gaia import Gaia

query = """
SELECT TOP 200
    source_id,
    ra,
    dec,
    ruwe,
    phot_g_mean_mag,
    bp_rp
FROM gaiadr3.gaia_source
WHERE ruwe > 2
AND phot_g_mean_mag < 20
ORDER BY ruwe DESC
"""

job = Gaia.launch_job(query)

results = job.get_results()

print(results[:20])

results.write(
    "weird_objects.csv",
    format="csv",
    overwrite=True
)