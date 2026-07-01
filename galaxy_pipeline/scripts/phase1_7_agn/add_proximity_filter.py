import pandas as pd
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

df = pd.read_csv("survivors.csv")
print(f"🔍 Checking {len(df)} survivors against known galaxy centers (30\" radius)...\n")

# Query HyperLEDA + NED galaxy catalogs
viz = Vizier(columns=["_RAJ2000", "_DEJ2000", "Name"])
galaxy_cats = viz.query_region(SkyCoord(ra=df["ra"].values*u.deg, dec=df["dec"].values*u.deg),
                               radius="30s", catalog=["VII/237/leda", "VII/269/ned"])

rejected = []
cleaned = []

for idx, row in df.iterrows():
    coord = SkyCoord(ra=row["ra"]*u.deg, dec=row["dec"]*u.deg)
    match_found = False
    for cat_name, table in galaxy_cats.items():
        if len(table) > 0:
            match_found = True
            rejected.append({**row.to_dict(), "reject_reason": f"Within 30\" of {table['Name'][0]}"})
            break
    if not match_found:
        cleaned.append(row.to_dict())
    time.sleep(1)

# Save outputs
pd.DataFrame(rejected).to_csv("rejected_proximity.csv", index=False)
clean_df = pd.DataFrame(cleaned)
clean_df.to_csv("cleaned_survivors.csv", index=False)

print("✅ PROXIMITY FILTER COMPLETE")
print(f"Rejected (near known galaxy): {len(rejected)}")
print(f"Cleaned survivors: {len(clean_df)}")
if len(clean_df) > 0:
    print("\n📌 Remaining candidates:")
    print(clean_df[["source_id", "ra", "dec", "score"]].to_string(index=False))