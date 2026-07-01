import pandas as pd

df = pd.read_csv("galaxy_candidates.csv")

df["score"] = (
    df["classprob_dsc_combmod_galaxy"]
    - df["classprob_dsc_combmod_star"]
    - df["classprob_dsc_combmod_quasar"]
)

top20 = df.sort_values("score", ascending=False).head(20)

print(
    top20[
        ["source_id", "ra", "dec", "classprob_dsc_combmod_galaxy",
         "classprob_dsc_combmod_star", "classprob_dsc_combmod_quasar", "score"]
    ].to_string(index=False)
)