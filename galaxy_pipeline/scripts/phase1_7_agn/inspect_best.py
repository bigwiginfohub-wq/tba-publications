import pandas as pd

df = pd.read_csv("gaia_candidates.csv")

best = df.sort_values("parallax").head(20)

print(best[[
    "source_id",
    "ra",
    "dec",
    "parallax",
    "pmra",
    "pmdec",
    "phot_g_mean_mag",
    "bp_rp"
]])