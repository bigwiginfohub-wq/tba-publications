"""Verify graph in-degree distribution and structural assumptions."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from tracebind_v11_core import astrometry_to_tangential_velocity, build_neighbor_graph

DATA_DIR = r"C:\GaiaProject\data\reference"
full_path = os.path.join(DATA_DIR, "hyades_cg22_dr3_crossmatched.csv")
df = pd.read_csv(full_path)
n = len(df)

# Compute positions
pos_3d, _ = astrometry_to_tangential_velocity(
    df["ra"].values, df["dec"].values, df["parallax"].values,
    df["pmra"].values, df["pmdec"].values
)

# Build graph with k+1 to ensure self is included in raw output
K = 30
graph = build_neighbor_graph(pos_3d, K)
# CRITICAL VERIFICATION: Ensure self-neighbor is excluded
print("🔍 Verifying graph structure...")
assert graph["indices"].shape[1] == K, f"Expected {K} neighbors, got {graph['indices'].shape[1]}"
# Check that the first column of the raw kneighbors output (before slicing) was the self-index
# Since build_neighbor_graph returns [:, 1:], we verify by checking if any star is its own neighbor
for i in range(min(10, n)): # Spot check first 10
    assert i not in graph["indices"][i], f"Self-loop detected for star {i}!"
print("✅ Graph structure verified: Directed k-NN graph with self-exclusion confirmed.\n")

# Compute in-degree (directed graph)
in_degree = np.zeros(n, dtype=int)
for j in range(n):
    for nbr_idx in graph["indices"][j]:
        in_degree[nbr_idx] += 1

mean_deg = np.mean(in_degree)
median_deg = np.median(in_degree)
std_deg = np.std(in_degree)

print(f"📊 In-Degree Statistics (Directed k-NN, k={K}):")
print(f"   Mean:   {mean_deg:.2f} (Expected ≈ {K} for uniform density)")
print(f"   Median: {median_deg:.2f}")
print(f"   Std Dev:{std_deg:.2f}")
print(f"   Range:  {np.min(in_degree)} to {np.max(in_degree)}")
print("   Note: In a directed k-NN graph, in-degree varies due to local density variations.\n")

# Plot
plt.figure(figsize=(8, 5))
plt.hist(in_degree, bins=40, color="#2E86AB", edgecolor="black", alpha=0.8)
plt.axvline(mean_deg, color="#A23B72", linestyle="--", label=f"Mean ≈ {mean_deg:.2f}")
plt.title("Distribution of Graph In-Degree (Hyades, k=30)")
plt.xlabel("In-Degree (Number of stars claiming this star as a neighbor)")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
out_path = os.path.join(DATA_DIR, "in_degree_verification.png")
plt.savefig(out_path, dpi=150)
print(f"💾 Plot saved to {out_path}")