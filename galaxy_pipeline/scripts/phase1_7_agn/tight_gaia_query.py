from astroquery.gaia import Gaia

query = """
SELECT TOP 100
    source_id, ra, dec,
    phot_g_mean_mag, bp_rp,
    parallax, parallax_error, pmra, pmdec, ruwe,
    classprob_dsc_combmod_galaxy,
    classprob_dsc_combmod_quasar,
    classprob_dsc_combmod_star
FROM gaiadr3.gaia_source
WHERE
    classprob_dsc_combmod_galaxy > 0.99
    AND classprob_dsc_combmod_star < 1e-8
    AND classprob_dsc_combmod_quasar < 1e-6
    AND ABS(parallax) < 0.5
    AND parallax_over_error < 1
    AND ABS(pmra) < 1
    AND ABS(pmdec) < 1
    AND phot_g_mean_mag BETWEEN 18 AND 22
    AND bp_rp BETWEEN 0.5 AND 0.7
    AND ruwe < 1.4
ORDER BY classprob_dsc_combmod_galaxy DESC
"""

print("Running tightened Gaia query...")
job = Gaia.launch_job(query)
res = job.get_results()
print(f"✅ Found {len(res)} high-confidence candidates.")
if len(res) > 0:
    res.write("tight_candidates.fits", overwrite=True)
    res.to_pandas().to_csv("tight_candidates.csv", index=False)
    print("📁 Saved to tight_candidates.fits & tight_candidates.csv")