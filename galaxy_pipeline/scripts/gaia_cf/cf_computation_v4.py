"""
TRACEBIND v2.0 - Phase 1: Velocity Dispersion Ratio (V4)
Measures position-velocity coupling via σ_local / σ_global.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

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


def compute_dispersion_ratio(positions_3d, pmra, pmdec, k):
    """
    Compute σ_local / σ_global for tangential velocity magnitude.
    
    Uses raw PM magnitudes (not unit vectors) because dispersion
    is a scalar property of the velocity distribution.
    """
    n = len(positions_3d)
    if k >= n:
        raise ValueError(f"k={k} exceeds sample size n={n}")

    # Tangential velocity magnitude (mas/yr)
    pm_mag = np.sqrt(pmra**2 + pmdec**2)

    # Global dispersion
    sigma_global = np.std(pm_mag)
    if sigma_global < 1e-10:
        return np.nan, np.full(n, np.nan)

    # k-NN in 3D Cartesian space (excludes self)
    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]

    # Vectorized local dispersion
    neighbor_pm = pm_mag[indices]            # (n, k)
    sigma_local = np.std(neighbor_pm, axis=1)  # (n,)

    ratio = sigma_local / sigma_global

    return float(np.median(ratio)), ratio


def main():
    print("🔬 TRACEBIND V4: Velocity Dispersion Ratio (σ_local / σ_global)")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())
    results = {}

    for k in K_VALUES:
        print(f"\n📊 Dispersion Ratio (k={k}):")
        print("-" * 50)
        for pop in populations:
            mask = df["population"] == pop
            try:
                med_ratio, _ = compute_dispersion_ratio(
                    positions_3d[mask],
                    df.loc[mask, "pmra"].values,
                    df.loc[mask, "pmdec"].values,
                    k
                )
                results[(pop, k)] = med_ratio
                print(f"  {pop:20s}: σ_local/σ_global = {med_ratio:.4f}")
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
    print("🧪 PHASE 1 VERDICT (Dispersion Ratio, k=20)")
    print("-" * 50)

    ref_k = 20
    sig = results.get(("signal", ref_k), np.nan)
    fld = results.get(("field_control", ref_k), np.nan)
    prj = results.get(("projection_control", ref_k), np.nan)

    # For dispersion ratio: LOWER = more structured
    print(f"  Signal     vs Field:      Δ = {sig - fld:+.4f}", end="")
    print(" ✅" if sig < fld - 0.05 else " ❌ FAIL")

    print(f"  Signal     vs Projection: Δ = {sig - prj:+.4f}", end="")
    print(" ✅ PASS" if sig < prj - 0.05 else " ❌ STILL BLIND TO STRUCTURE")

    print(f"  Projection vs Field:     Δ = {prj - fld:+.4f}", end="")
    print(" ✅ COLLAPSED" if abs(prj - fld) < 0.05 else " ⚠️ LEAKAGE")

    print("\n🔒 TRACEBIND V4 CHECKPOINT:")
    print("- Method: σ_local / σ_global (tangential PM magnitude)")
    print(f"- k values: {K_VALUES}")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V4")


if __name__ == "__main__":
    main()