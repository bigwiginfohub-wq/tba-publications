from astroquery.gaia import Gaia

query = """
SELECT
 source_id,
 ruwe,
 ipd_gof_harmonic_amplitude,
 ipd_frac_multi_peak,
 phot_g_mean_mag,
 phot_g_mean_flux_over_error
FROM gaiadr3.gaia_source
WHERE source_id = 3663219731798361600
"""

job = Gaia.launch_job(query)
result = job.get_results()

if len(result) > 0:
    print("GAIA MORPHOLOGY DATA:")
    for col in result.colnames:
        print(f"  {col}: {result[col][0]}")
else:
    print("NO GAIA DATA RETURNED.")