"""
TRACEBIND v2.0 - Phase 1: Permutation-Based Dispersion Ratio (V5)
Tests whether local velocity dispersion is lower than expected by chance.
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
N_PERMUTATIONS = 50
RANDOM_SEED = 42


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def compute_dispersion_ratio(positions_3d, pm_mag, k):
    """Compute median(σ_local / σ_global) for PM magnitudes."""
    n = len(positions_3d)
    if k >= n:
        raise ValueError(f"k={k} exceeds sample size n={n}")

    sigma_global = np.std(pm_mag)
    if sigma_global < 1e-10:
        return np.nan

    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]

    neighbor_pm = pm_mag[indices]
    sigma_local = np.std(neighbor_pm, axis=1)
    ratio = sigma_local / sigma_global

    return float(np.median(ratio))


def compute_permutation_zscore(positions_3d, pmra, pmdec, k, n_perm, seed):
    """
    Compute real dispersion ratio and its significance via permutation test.
    
    Returns:
        real_ratio, z_score, mean_null_ratio, std_null_ratio
    """
    pm_mag = np.sqrt(pmra**2 + pmdec**2)
    real_ratio = compute_dispersion_ratio(positions_3d, pm_mag, k)

    if np.isnan(real_ratio):
        return np.nan, np.nan, np.nan, np.nan

    rng = np.random.default_rng(seed)
    null_ratios = []

    for _ in range(n_perm):
        # Shuffle velocities independently to break position-velocity coupling
        perm_idx = rng.permutation(len(pmra))
        shuffled_pm_mag = np.sqrt(pmra[perm_idx]**2 + pmdec[perm_idx]**2)
        null_ratio = compute_dispersion_ratio(positions_3d, shuffled_pm_mag, k)
        if not np.isnan(null_ratio):
            null_ratios.append(null_ratio)

    if len(null_ratios) < 5:
        return real_ratio, np.nan, np.nan, np.nan

    mean_null = np.mean(null_ratios)
    std_null = np.std(null_ratios)
    z_score = (real_ratio - mean_null) / std_null if std_null > 1e-10 else np.nan

    return real_ratio, z_score, mean_null, std_null


def main():
    print("🔬 TRACEBIND V5: Permutation-Based Dispersion Ratio")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows | Permutations: {N_PERMUTATIONS} | Seed: {RANDOM_SEED}\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())
    results = {}

    ref_k = 20
    print(f"📊 Results for k={ref_k}:")
    print("-" * 70)
    print(f"  {'Population':<20s} {'Real Ratio':>10s} {'Null Mean':>10s} {'Z-Score':>10s} {'Verdict':>12s}")
    print("-" * 70)

    for pop in populations:
        mask = df["population"] == pop
        try:
            real_r, z, null_mean, null_std = compute_permutation_zscore(
                positions_3d[mask],
                df.loc[mask, "pmra"].values,
                df.loc[mask, "pmdec"].values,
                ref_k, N_PERMUTATIONS, RANDOM_SEED
            )
            results[pop] = {"real": real_r, "z": z, "null_mean": null_mean}

            # Verdict logic: significantly LOWER than null = structured
            if not np.isnan(z):
                verdict = "✅ STRUCTURED" if z < -2.0 else ("⚠️ MARGINAL" if z < -1.5 else "❌ NULL")
            else:
                verdict = "ERROR"

            print(f"  {pop:<20s} {real_r:>10.4f} {null_mean:>10.4f} {z:>10.3f} {verdict:>12s}")
        except ValueError as e:
            print(f"  {pop:<20s} ERROR: {e}")
            results[pop] = {"real": np.nan, "z": np.nan, "null_mean": np.nan}

    # === CROSS-POPULATION VERDICT ===
    print("\n" + "=" * 70)
    print("🧪 PHASE 1 FINAL VERDICT (Permutation Z-Scores)")
    print("-" * 50)

    sig_z = results.get("signal", {}).get("z", np.nan)
    prj_z = results.get("projection_control", {}).get("z", np.nan)
    fld_z = results.get("field_control", {}).get("z", np.nan)

    sig_real = results.get("signal", {}).get("real", np.nan)
    prj_real = results.get("projection_control", {}).get("real", np.nan)

    print(f"  Signal Z-score:     {sig_z:+.3f}", end="")
    print(" ✅ SIGNIFICANT" if sig_z < -2.0 else " ❌ NOT SIGNIFICANT")

    print(f"  Projection Z-score: {prj_z:+.3f}", end="")
    print(" ✅ NULL (expected)" if abs(prj_z) < 2.0 else " ⚠️ UNEXPECTED SIGNAL")

    print(f"  Field Z-score:      {fld_z:+.3f}", end="")
    print(" ✅ NULL (expected)" if abs(fld_z) < 2.0 else " ⚠️ UNEXPECTED SIGNAL")

    if not np.isnan(sig_z) and not np.isnan(prj_z):
        separation = sig_z - prj_z
        print(f"\n  Signal vs Projection Z-separation: {separation:+.3f}", end="")
        print(" ✅ PASS" if separation < -2.0 else " ❌ FAIL")

    print("\n🔒 TRACEBIND V5 CHECKPOINT:")
    print(f"- Method: σ_local/σ_global + {N_PERMUTATIONS}-trial permutation baseline")
    print(f"- Significance threshold: Z < -2.0 (one-tailed)")
    print(f"- k reference: {ref_k}")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V5")


if __name__ == "__main__":
    main()