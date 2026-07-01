from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import pandas as pd

df = pd.read_csv("galaxy_candidates.csv")

row = df.iloc[0]

coord = SkyCoord(
    ra=row["ra"]*u.deg,
    dec=row["dec"]*u.deg
)

result = Simbad.query_region(
    coord,
    radius="5s"
)

print(result)

if result is not None:
    print("\nColumns:")
    print(result.colnames)