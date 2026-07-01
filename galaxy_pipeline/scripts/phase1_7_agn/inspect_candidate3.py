from astroquery.gaia import Gaia

source_id = 3663219731798361600

query = f"""
SELECT
    source_id,
    ra,
    dec,
    parallax,
    parallax_error,
    pmra,
    pmdec,
    ruwe,
    phot_g_mean_mag,
    bp_rp,
    classprob_dsc_combmod_galaxy,
    classprob_dsc_combmod_star,
    classprob_dsc_combmod_quasar
FROM gaiadr3.gaia_source
WHERE source_id = {source_id}
"""

job = Gaia.launch_job(query)

print(job.get_results())