from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import pandas as pd

df = pd.read_csv("galaxy_candidates.csv")

for i, row in df.head(20).iterrows():

    coord = SkyCoord(
        ra=row["ra"]*u.deg,
        dec=row["dec"]*u.deg
    )

    try:
        result = Simbad.query_region(
            coord,
            radius="5s"
        )

        print("\n-------------------")
        print("Candidate", i)
        print("Source ID:", row["source_id"])

        if result is None:
            print("NOT FOUND IN SIMBAD")
        else:
            print("FOUND:")
            print(result["main_id"])

    except Exception as e:
        print("ERROR:", e)