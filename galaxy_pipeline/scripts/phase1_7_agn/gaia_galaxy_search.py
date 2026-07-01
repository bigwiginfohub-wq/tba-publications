from astroquery.gaia import Gaia

query = """
SELECT TOP 500
    source_id,
    ra,
    dec,
    phot_g_mean_mag,
    bp_rp,
    parallax,
    parallax_error,
    parallax_over_error,
    pmra,
    pmdec,
    ruwe,
    classprob_dsc_combmod_galaxy,
    classprob_dsc_combmod_quasar,
    classprob_dsc_combmod_star
FROM gaiadr3.gaia_source
WHERE
    ABS(parallax) < 0.5
    AND parallax_over_error < 1
    AND ABS(pmra) < 1
    AND ABS(pmdec) < 1
    AND phot_g_mean_mag BETWEEN 18 AND 22
    AND bp_rp BETWEEN 0.5 AND 0.7
    AND ruwe < 1.4
    AND classprob_dsc_combmod_galaxy > 0.5
ORDER BY classprob_dsc_combmod_galaxy DESC
"""

job = Gaia.launch_job(query)
results = job.get_results()

print(results[:10])

results.write("galaxy_candidates.fits", overwrite=True)
print("Candidates:", len(results))

df = results.to_pandas()
df.to_csv("galaxy_candidates.csv", index=False)