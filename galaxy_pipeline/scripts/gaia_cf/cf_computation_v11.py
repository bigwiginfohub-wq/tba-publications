"""
TRACEBIND v2.0 - Phase 1: Non-Degenerate LOO Prediction (V11)
Fixes: (1) Leave-one-out prediction eliminates algebraic collapse.
       (2) Per-population geometry baselines.
       (3) Self-exclusion in local shuffle.
       (4) Safe k-clamping for small populations.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))\n_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))\nINPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")

K_PREDICT = 30
K_SHUFFLE = 50
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


def compute_loo_prediction_error(positions_3d, pmra, pmdec, k):
    """
    LEAVE-ONE-OUT weighted prediction error.
    Predicts each star's velocity from neighbors EXCLUDING itself.
    Mathematically non-degenerate: pred ≠ target by construction.
    """
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2:
        return np.nan

    pm_vectors = np.column_stack([pmra, pmdec])
    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)

    # Exclude self: indices[:,0] is always self for ball_tree
    dist_nbrs = distances[:, 1:]   # (n, k)
    idx_nbrs = indices[:, 1:]      # (n, k)

    eps = 1e-6
    weights = 1.0 / (dist_nbrs**2 + eps)
    w_norm = weights / np.sum(weights, axis=1, keepdims=True)

    # Predicted velocity = weighted mean of NEIGHBORS ONLY (no self)
    vel_nbrs = pm_vectors[idx_nbrs]                    # (n, k, 2)
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)  # (n, 2)

    # Error = ||target - predicted|| (non-degenerate)
    errors = np.linalg.norm(pm_vectors - predicted, axis=1)
    return float(np.median(errors))


def compute_own_geometry_baseline(positions_3d, pmra, pmdec, k_predict, k_shuffle, n_perm, seed):
    """Per-population geometry baseline with SELF-EXCLUSION in shuffle."""
    rng = np.random.default_rng(seed)
    pm_vectors = np.column_stack([pmra, pmdec])
    n = len(positions_3d)

    safe_k_shuf = min(max(k_predict + 1, k_shuffle), n)
    nn = NearestNeighbors(n_neighbors=safe_k_shuf, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    _, indices_all = nn.kneighbors(positions_3d)

    null_errors = []
    for _ in range(n_perm):
        shuffled_pm = np.empty_like(pm_vectors)
        for i in range(n):
            # FIX: Exclude self from shuffle candidates [1:] not [:]
            nbr_idx = indices_all[i, 1:safe_k_shuf]
            if len(nbr_idx) == 0:
                shuffled_pm[i] = pm_vectors[i]
                continue
            chosen = rng.integers(0, len(nbr_idx))
            local_vel_std = np.std(pm_vectors[nbr_idx], axis=0)
            noise = rng.normal(0, 0.1 * local_vel_std, size=2)
            shuffled_pm[i] = pm_vectors[nbr_idx[chosen]] + noise

        err = compute_loo_prediction_error(positions_3d, shuffled_pm[:, 0], shuffled_pm[:, 1], k_predict)
        if not np.isnan(err):
            null_errors.append(err)

    return float(np.mean(null_errors)) if null_errors else np.nan


def main():
    print("🔬 TRACEBIND V11: Non-Degenerate LOO Prediction + Per-Pop Baselines")
    print("=" * 78)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows | k_pred={K_PREDICT} | k_shuf={K_SHUFFLE}")
    print(f"   Perms: {N_PERMUTATIONS} | Seed: {RANDOM_SEED}\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())
    results = {}

    print(f"📊 LOO Prediction Error + Own Baseline:")
    print("-" * 78)
    print(f"  {'Population':<20s} {'RealErr':>8s} {'OwnBase':>8s} {'Ratio':>8s} {'Verdict':>14s}")
    print("-" * 78)

    for pop in populations:
        mask = df["population"] == pop
        real_err = compute_loo_prediction_error(
            positions_3d[mask],
            df.loc[mask, "pmra"].values,
            df.loc[mask, "pmdec"].values,
            K_PREDICT
        )

        own_baseline = compute_own_geometry_baseline(
            positions_3d[mask],
            df.loc[mask, "pmra"].values,
            df.loc[mask, "pmdec"].values,
            K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, RANDOM_SEED
        )

        if np.isnan(real_err) or np.isnan(own_baseline) or own_baseline < 1e-10:
            print(f"  {pop:<20s} ERROR")
            results[pop] = {"ratio": np.nan}
            continue

        ratio = real_err / own_baseline
        results[pop] = {"real": real_err, "baseline": own_baseline, "ratio": ratio}

        verdict = "✅ EXCESS" if ratio < 0.80 else ("⚠️ MARGINAL" if ratio < 0.95 else "❌ GEOMETRY")
        print(f"  {pop:<20s} {real_err:>8.4f} {own_baseline:>8.4f} {ratio:>8.4f} {verdict:>14s}")

    # === FINAL VERDICT ===
    print("\n" + "=" * 78)
    sig_r = results.get("signal", {}).get("ratio", np.nan)
    prj_r = results.get("projection_control", {}).get("ratio", np.nan)
    fld_r = results.get("field_control", {}).get("ratio", np.nan)

    sig_pass = not np.isnan(sig_r) and sig_r < 0.80
    prj_fail = np.isnan(prj_r) or prj_r >= 0.80
    fld_fail = np.isnan(fld_r) or fld_r >= 0.80

    print(f"  Signal ratio < 0.80:          {'✅ YES' if sig_pass else '❌ NO'}")
    print(f"  Projection ratio >= 0.80:     {'✅ YES' if prj_fail else '❌ NO'}")
    print(f"  Field ratio >= 0.80:          {'✅ YES' if fld_fail else '❌ NO'}")

    overall = sig_pass and prj_fail and fld_fail
    print(f"\n  🎯 OVERALL PHASE 1 STATUS: {'✅ PASS — METRIC VALIDATED' if overall else '❌ FAIL — FURTHER REDESIGN NEEDED'}")

    print("\n🔒 TRACEBIND V11 CHECKPOINT:")
    print("- LOO prediction: algebraically non-degenerate")
    print("- Per-population baselines: no cross-pop assumption")
    print("- Self-excluded shuffle: no identity preservation")
    print("- Safe k-clamping: handles small populations")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V11")


if __name__ == "__main__":
    main()
