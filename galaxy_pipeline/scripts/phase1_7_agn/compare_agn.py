import pandas as pd

candidates = pd.read_csv("gaia_candidates.csv")

print()
print("Candidate count:", len(candidates))
print()

print("Lowest parallax objects")
print(
    candidates.sort_values("parallax")
    [["source_id","parallax","phot_g_mean_mag","bp_rp"]]
    .head(10)
)