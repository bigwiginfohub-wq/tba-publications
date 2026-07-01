import pandas as pd

df = pd.read_csv("galaxy_candidates.csv")

print("Total candidates:", len(df))

print("\nPotentially interesting:")

for i,row in df.head(50).iterrows():

    print(
        row["source_id"],
        row["ra"],
        row["dec"]
    )