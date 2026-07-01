from astroquery.gaia import Gaia

source_id = 141419666601293056

query = f"""
SELECT *
FROM gaiadr3.gaia_source
WHERE source_id = {source_id}
"""

job = Gaia.launch_job(query)

result = job.get_results()

print(result)