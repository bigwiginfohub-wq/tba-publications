from astroquery.gaia import Gaia

query = """
SELECT TOP 100
    source_id,
    ra,
    dec,
    phot_g_mean_mag,
    classprob_dsc_combmod_quasar,
    classprob_dsc_combmod_star
FROM gaiadr3.gaia_source
WHERE classprob_dsc_combmod_quasar > 0.95
AND phot_g_mean_mag > 18
ORDER BY classprob_dsc_combmod_quasar DESC
"""

job = Gaia.launch_job(query)

results = job.get_results()

print(results)

results.write(
    "quasar_candidates.csv",
    format="csv",
    overwrite=True
)

print("Saved quasar_candidates.csv")