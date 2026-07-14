"""Summarize TRACEBIND V11 Robustness Audit Results."""
import pandas as pd
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
AUDIT_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "tracebind_v11_audit_results.csv")

if not os.path.exists(AUDIT_CSV):
    raise FileNotFoundError(f"Audit results not found at {AUDIT_CSV}")

df = pd.read_csv(AUDIT_CSV)

# Input Validation
required = ["R_pleiades", "R_hyades", "R_difference", "k", "noise_frac"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns in audit CSV: {missing}")

print("📊 TRACEBIND V11 ROBUSTNESS SUMMARY")
print("=" * 80)
print(f"Total audit runs: {len(df)}")

# Cluster-level stability
for col_prefix in ["R_pleiades", "R_hyades"]:
    name = "Pleiades" if "pleiades" in col_prefix else "Hyades"
    vals = df[col_prefix]
    print(f"\n{name} Stability:")
    print(f"   Mean R : {vals.mean():.4f}")
    print(f"   Std R  : {vals.std(ddof=0):.4f}") # Population std
    print(f"   95% CI : [{vals.quantile(0.025):.4f}, {vals.quantile(0.975):.4f}]")

# Difference stability
diff = df["R_difference"]
print(f"\nDifference (Pleiades - Hyades) Stability:")
print(f"   Mean Diff : {diff.mean():.4f}")
print(f"   Std Diff  : {diff.std(ddof=0):.4f}") # Population std
print(f"   Min Diff  : {diff.min():.4f}")

# Explicit ordering check
ordering_count = (df["R_difference"] > 0).sum()
total_runs = len(df)
print(f"\nOrdering preserved in {ordering_count}/{total_runs} runs.")

# Parameter Sensitivity
print("\nMean R by Neighborhood Size (k):")
print(df.groupby("k")[["R_pleiades", "R_hyades"]].mean().round(4))

print("\nMean R by Noise Fraction:")
print(df.groupby("noise_frac")[["R_pleiades", "R_hyades"]].mean().round(4))

# Scientific Interpretation
if (diff > 0).all():
    print("\nInterpretation:")
    print(
        "Across all tested parameter combinations, the Hyades "
        "maintained a lower coherence ratio than the Pleiades, "
        "indicating that the comparative ordering is robust to "
        "the tested choices of neighborhood size, noise fraction, "
        "and random seed."
    )
else:
    print("\n⚠️ Warning: Ordering was not preserved in all runs.")

print("\n✅ Summary Complete.")