from astroquery.gaia import Gaia
import pandas as pd

query = """
SELECT TOP 100
    source_id,
    ra,
    dec,
    phot_g_mean_mag,
    bp_rp,
    parallax,
    pmra,
    pmdec
FROM gaiadr3.gaia_source
WHERE ABS(parallax) < 0.2
AND ABS(pmra) < 0.5
AND ABS(pmdec) < 0.5
AND phot_g_mean_mag > 18
"""

# Run query
job = Gaia.launch_job(query)

# Retrieve results
results = job.get_results()

# Convert to DataFrame
df = results.to_pandas()

# Save CSV
df.to_csv(
    "gaia_candidates.csv",
    index=False
)

# Preview
print(df.head())

print(f"Found {len(results)} sources")