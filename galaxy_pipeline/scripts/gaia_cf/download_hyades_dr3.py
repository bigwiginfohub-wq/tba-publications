from astroquery.gaia import Gaia
import pandas as pd
import os


OUT = r"C:\GaiaProject\data\reference\hyades_gaia_dr3.csv"


query = """
SELECT
source_id,
ra,
dec,
parallax,
pmra,
pmdec,
phot_g_mean_mag,
ruwe,
parallax_error,
pmra_error,
pmdec_error
FROM gaiadr3.gaia_source

WHERE

ra BETWEEN 50 AND 70
AND dec BETWEEN 5 AND 25

AND parallax BETWEEN 15 AND 30

AND parallax_over_error > 10

AND phot_g_mean_mag < 18

AND ruwe < 1.4

"""


print("Querying Gaia DR3 Hyades region")

job = Gaia.launch_job(query)

df = job.get_results().to_pandas()


print("Downloaded:", len(df))


df.to_csv(
    OUT,
    index=False
)

print("Saved:", OUT)

print(
"Median distance:",
(1000/df.parallax).median()
)