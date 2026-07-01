from astroquery.gaia import Gaia

query = """
SELECT TOP 100
    g.source_id,
    g.ra,
    g.dec,
    g.phot_g_mean_mag,
    g.bp_rp
FROM gaiadr3.gaia_source AS g
JOIN gaiadr3.agn_cross_id AS a
ON g.source_id = a.source_id
"""

job = Gaia.launch_job(query)
results = job.get_results()

print(results[:20])