import pandas as pd

df = pd.read_csv("unknown_candidates.csv")

score = (
    df["classprob_dsc_combmod_galaxy"]
    - df["classprob_dsc_combmod_star"]
    - df["classprob_dsc_combmod_quasar"]
)

df["score"] = score

best = df.sort_values(
    "score",
    ascending=False
)

print(best.head(20))

best.to_csv(
    "best_unknowns.csv",
    index=False
)