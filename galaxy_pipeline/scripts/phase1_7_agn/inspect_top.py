import pandas as pd

df = pd.read_csv("galaxy_candidates.csv")

print(
    df.sort_values(
        "classprob_dsc_combmod_galaxy",
        ascending=False
    ).head(20)
)