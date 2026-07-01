from astroquery.gaia import Gaia

source_id = 141681075491760640

query = f"""
SELECT *
FROM gaiadr3.qso_candidates
WHERE source_id = {source_id}
"""

job = Gaia.launch_job(query)

print(job.get_results())