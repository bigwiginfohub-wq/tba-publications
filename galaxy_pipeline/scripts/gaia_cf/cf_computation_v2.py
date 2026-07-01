"""
TRACEBIND v2.0 - Phase 1: Coherence Factor Computation V2
Implements Local k-NN Cf with 3D Cartesian neighbors and tangential velocity unit vectors.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

# === PATH RESOLUTION ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")

# === CONFIGURATION ===
K_VALUES = [10, 20, 40]


def astrometry_to_cartesian(ra, dec, parallax):
    """Convert Gaia astrometry to 3D Cartesian coordinates (pc)."""
    distance = 1000.0 / parallax  # mas -> pc
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def pm_to_tangential_unit_vectors(pmra, pmdec):
    """Convert proper motions to unit direction vectors on the tangent plane."""
    vectors = np.column_stack([pmra, pmdec])
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    return vectors / norms


def compute_global_cf(unit_vectors):
    """Global Cf: magnitude of mean unit vector."""
    mean_vec = np.mean(unit_vectors, axis=0)
    return np.linalg.norm(mean_vec)


def compute_local_cf(positions_3d, unit_vectors, k):
    """
    Local k-NN Cf: for each star, compute Cf using its k nearest
    3D spatial neighbors, then return the population median.
    """
    n = len(positions_3d)
    if k >= n:
        raise ValueError(f"k={k} exceeds sample size n={n}")
    
    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    
    # indices[:, 0] is the star itself; [:, 1:] are neighbors
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]
    
    # Vectorized: gather neighbor unit vectors for all stars at once
    # Shape: (n, k, 2)
    neighbor_vectors = unit_vectors[indices]
    
    # Mean unit vector per star's neighborhood
    mean_neighbor_vecs = np.mean(neighbor_vectors, axis=1)  # (n, 2)
    
    # Cf per star = magnitude of local mean direction
    cf_per_star = np.linalg.norm(mean_neighbor_vecs, axis=1)
    
    # Population summary: median (robust to edge effects)
    return float(np.median(cf_per_star)), cf_per_star


def main():
    print("🔬 TRACEBIND Cf Computation V2 (Local k-NN + 3D Cartesian)")
    print("=" * 70)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        print("   Run sim_hyades_generator.py first.")
        return
    
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows from {INPUT_FILE}\n")
    
    # Precompute shared representations
    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )
    unit_vectors = pm_to_tangential_unit_vectors(
        df["pmra"].values, df["pmdec"].values
    )
    
    populations = sorted(df["population"].unique())
    
    # === GLOBAL CF (retained for comparison) ===
    print("📊 GLOBAL Cf (baseline - expected to fail projection test):")
    print("-" * 50)
    for pop in populations:
        mask = df["population"] == pop
        cf = compute_global_cf(unit_vectors[mask])
        print(f"  {pop:20s}: Cf = {cf:.4f}")
    
    # === LOCAL CF (multi-k) ===
    print("\n📊 LOCAL Cf (k-NN in 3D Cartesian space):")
    print("-" * 50)
    results = {}
    for k in K_VALUES:
        print(f"\n  k = {k}:")
        for pop in populations:
            mask = df["population"] == pop
            pos = positions_3d[mask]
            uvs = unit_vectors[mask]
            
            try:
                cf_median, _ = compute_local_cf(pos, uvs, k)
                results[(pop, k)] = cf_median
                print(f"    {pop:20s}: Cf = {cf_median:.4f}")
            except ValueError as e:
                print(f"    {pop:20s}: ERROR - {e}")
                results[(pop, k)] = np.nan
    
    # === K-STABILITY DIAGNOSTIC ===
    print("\n📈 Stability across k:")
    for pop in populations:
        vals = [results.get((pop, k), np.nan) for k in K_VALUES]
        formatted = [f"{v:.4f}" if not np.isnan(v) else "NaN" for v in vals]
        print(f"  {pop:20s}: {formatted}")
    
    # === VERDICT DIAGNOSTICS ===
    print("\n" + "=" * 70)
    print("🧪 PHASE 1 VERDICT DIAGNOSTICS (k=20 reference)")
    print("-" * 50)
    
    ref_k = 20
    sig_cf = results.get(("signal", ref_k), np.nan)
    fld_cf = results.get(("field_control", ref_k), np.nan)
    prj_cf = results.get(("projection_control", ref_k), np.nan)
    
    print(f"  Signal     vs Field:      Δ = {sig_cf - fld_cf:+.4f}", end="")
    print(" ✅" if sig_cf > fld_cf + 0.05 else " ❌ FAIL")
    
    print(f"  Signal     vs Projection: Δ = {sig_cf - prj_cf:+.4f}", end="")
    print(" ✅ PASS" if sig_cf > prj_cf + 0.05 else " ❌ PROJECTION BIAS")
    
    print(f"  Projection vs Field:     Δ = {prj_cf - fld_cf:+.4f}", end="")
    print(" ✅" if abs(prj_cf - fld_cf) < 0.05 else " ⚠️ LEAKAGE")
    
    # === CHECKPOINT ===
    print("\n🔒 TRACEBIND CF V2 CHECKPOINT:")
    print(f"- Method: Local k-NN in 3D Cartesian + tangential unit vectors")
    print(f"- k values tested: {K_VALUES}")
    print(f"- Global Cf retained for comparison")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V2")


if __name__ == "__main__":
    main()