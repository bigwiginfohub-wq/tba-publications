from astroquery.gaia import Gaia

source_id = 141681075491760640

query = f"""
SELECT
source_id,
ra,
dec,
ruwe,
phot_g_mean_mag,
bp_rp,
teff_gspphot,
distance_gspphot,
classprob_dsc_combmod_quasar,
classprob_dsc_combmod_galaxy,
classprob_dsc_combmod_star
FROM gaiadr3.gaia_source
WHERE source_id = {source_id}
"""

job = Gaia.launch_job(query)

print(job.get_results())