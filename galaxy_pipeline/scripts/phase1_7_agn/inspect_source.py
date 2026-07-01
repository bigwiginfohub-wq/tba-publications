from astroquery.gaia import Gaia

source_id = 141681075491760640

query = f"""
SELECT
    source_id,
    parallax,
    parallax_error,
    parallax_over_error,
    pmra,
    pmra_error,
    pmdec,
    pmdec_error,
    ruwe,
    phot_g_mean_mag,
    bp_rp
FROM gaiadr3.gaia_source
WHERE source_id = {source_id}
"""

job = Gaia.launch_job(query)

print(job.get_results())