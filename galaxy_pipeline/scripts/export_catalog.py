import pandas as pd

# Load ranked results
df = pd.read_csv("data/batch_ranked_candidates.csv")

# Filter T1 & T2
catalog = df[df["tier"].isin(["T1_STRONG_GALAXY", "T2_PROBABLE_GALAXY"])].copy()

# Clean columns for scientific use
catalog = catalog[["rank", "source_id", "ra", "dec", "priority_score", "tier", 
                   "gaia_astrometry_snr", "ps1_extension", "ps1_color", "dsc_probs"]]

# Format source_id as integer string (avoid scientific notation)
catalog["source_id"] = catalog["source_id"].astype(str).str.replace(".0", "", regex=False)

# Save
catalog.to_csv("data/candidate_catalog.csv", index=False)
print(f"✅ Exported {len(catalog)} candidates to data/candidate_catalog.csv")