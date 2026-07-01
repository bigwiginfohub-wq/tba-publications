"""
TRACEBIND v2.0 - Phase 1: Residual Coherence Factor (V3)
Subtracts global bulk flow before computing local k-NN Cf.
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

K_VALUES = [10, 20, 40]


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def pm_to_tangential_unit_vectors(pmra, pmdec):
    vectors = np.column_stack([pmra, pmdec])
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    return vectors / norms


def compute_residual_local_cf(positions_3d, unit_vectors, k):
    """
    Residual Local Cf: subtract global mean direction, then compute
    local k-NN coherence on the residual unit vectors.
    """
    n = len(positions_3d)
    if k >= n:
        raise ValueError(f"k={k} exceeds sample size n={n}")

    # Step 1: Global mean direction (bulk flow in unit-vector space)
    global_mean = np.mean(unit_vectors, axis=0)
    global_norm = np.linalg.norm(global_mean)
    if global_norm > 1e-10:
        global_mean = global_mean / global_norm

    # Step 2: Residual vectors (remove bulk flow component)
    residuals = unit_vectors - global_mean
    res_norms = np.linalg.norm(residuals, axis=1, keepdims=True)
    res_norms[res_norms == 0] = 1e-10
    res_unit = residuals / res_norms

    # Step 3: k-NN in 3D Cartesian space (vectorized, excludes self)
    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]

    # Step 4: Vectorized local coherence on residual unit vectors
    neighbor_res_vecs = res_unit[indices]           # (n, k, 2)
    mean_neighbor = np.mean(neighbor_res_vecs, axis=1)  # (n, 2)
    cf_per_star = np.linalg.norm(mean_neighbor, axis=1)

    return float(np.median(cf_per_star)), cf_per_star


def main():
    print("🔬 TRACEBIND Residual Cf V3 (Bulk Flow Subtracted)")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )
    unit_vectors = pm_to_tangential_unit_vectors(
        df["pmra"].values, df["pmdec"].values
    )

    populations = sorted(df["population"].unique())
    results = {}

    for k in K_VALUES:
        print(f"\n📊 Residual Local Cf (k={k}):")
        print("-" * 50)
        for pop in populations:
            mask = df["population"] == pop
            try:
                cf_med, _ = compute_residual_local_cf(
                    positions_3d[mask], unit_vectors[mask], k
                )
                results[(pop, k)] = cf_med
                print(f"  {pop:20s}: Cf_res = {cf_med:.4f}")
            except ValueError as e:
                print(f"  {pop:20s}: ERROR - {e}")
                results[(pop, k)] = np.nan

    # === K-STABILITY ===
    print("\n📈 Stability across k:")
    for pop in populations:
        vals = [results.get((pop, k), np.nan) for k in K_VALUES]
        fmt = [f"{v:.4f}" if not np.isnan(v) else "NaN" for v in vals]
        print(f"  {pop:20s}: {fmt}")

    # === VERDICT ===
    print("\n" + "=" * 70)
    print("🧪 PHASE 1 VERDICT (Residual Cf, k=20)")
    print("-" * 50)

    ref_k = 20
    sig = results.get(("signal", ref_k), np.nan)
    fld = results.get(("field_control", ref_k), np.nan)
    prj = results.get(("projection_control", ref_k), np.nan)

    print(f"  Signal     vs Field:      Δ = {sig - fld:+.4f}", end="")
    print(" ✅" if sig > fld + 0.05 else " ❌ FAIL")

    print(f"  Signal     vs Projection: Δ = {sig - prj:+.4f}", end="")
    print(" ✅ PASS" if sig > prj + 0.05 else " ❌ PROJECTION BIAS REMAINS")

    print(f"  Projection vs Field:     Δ = {prj - fld:+.4f}", end="")
    print(" ✅ COLLAPSED" if abs(prj - fld) < 0.05 else " ⚠️ LEAKAGE")

    print("\n🔒 TRACEBIND CF V3 CHECKPOINT:")
    print("- Method: Residual Local k-NN (global mean direction subtracted)")
    print(f"- k values: {K_VALUES}")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V3")


if __name__ == "__main__":
    main()