import pandas as pd
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

df = pd.read_csv("galaxy_candidates.csv")

unknowns = []

for i,row in df.head(100).iterrows():

    print(f"Checking {i}")

    coord = SkyCoord(
        ra=row["ra"]*u.deg,
        dec=row["dec"]*u.deg
    )

    try:
        result = Simbad.query_region(
            coord,
            radius="5s"
        )

        if result is None or len(result) == 0:
            unknowns.append(row)

    except:
        pass

    time.sleep(1)

pd.DataFrame(unknowns).to_csv(
    "unknown_candidates.csv",
    index=False
)

print("Unknown candidates:", len(unknowns))

import pandas as pd

df = pd.read_csv("unknown_candidates.csv")

print(df.head(10))
print()
print("Count =", len(df))