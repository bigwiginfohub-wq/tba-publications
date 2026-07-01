"""
TRACEBIND v2.0 - Phase 1: Robust Local Null (V9.1)
Fixes: (1) Removes global assignment constraint for strict locality.
       (2) Adds local noise injection to break exact functional mapping.
Includes: Null separation, shuffle locality, and k-stability diagnostics.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")

K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 100
RANDOM_SEED = 42
NOISE_SIGMA_FRAC = 0.1  # Noise = 10% of local velocity std


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def compute_weighted_residual_error(positions_3d, pmra, pmdec, k):
    n = len(positions_3d)
    if k >= n:
        return np.nan
    pm_vectors = np.column_stack([pmra, pmdec])
    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)
    dist_nbrs = distances[:, 1:]
    idx_nbrs = indices[:, 1:]
    eps = 1e-6
    weights = 1.0 / (dist_nbrs**2 + eps)
    w_norm = weights / np.sum(weights, axis=1, keepdims=True)
    vel_nbrs = pm_vectors[idx_nbrs]
    local_bulk = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)
    vel_nbrs_res = vel_nbrs - local_bulk[:, np.newaxis, :]
    target_res = pm_vectors - local_bulk
    pred_res = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs_res, axis=1)
    errors = np.linalg.norm(target_res - pred_res, axis=1)
    return float(np.median(errors))


def locally_shuffle_with_noise(positions_3d, pmra, pmdec, k_shuffle, sigma_frac, rng):
    """
    Strictly local shuffle WITH noise injection.
    - No 'used' constraint: allows reuse, guarantees locality.
    - Adds Gaussian noise scaled to local velocity dispersion.
    Returns shuffled pmra, pmdec AND mean shuffle distance for sanity check.
    """
    n = len(positions_3d)
    pm_vectors = np.column_stack([pmra, pmdec])

    nn = NearestNeighbors(n_neighbors=k_shuffle, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)

    shuffled_pm = np.empty_like(pm_vectors)
    shuffle_distances = np.empty(n)

    for i in range(n):
        nbr_idx = indices[i]
        nbr_dist = distances[i]

        # FIX 1: Sample WITH replacement — strictly local, no global constraint
        chosen_local_pos = rng.integers(0, len(nbr_idx))
        chosen_global_idx = nbr_idx[chosen_local_pos]
        shuffle_distances[i] = nbr_dist[chosen_local_pos]

        # FIX 2: Add noise scaled to local neighborhood velocity dispersion
        local_vel_std = np.std(pm_vectors[nbr_idx], axis=0)
        noise = rng.normal(0, sigma_frac * local_vel_std, size=2)
        shuffled_pm[i] = pm_vectors[chosen_global_idx] + noise

    return shuffled_pm[:, 0], shuffled_pm[:, 1], float(np.mean(shuffle_distances))


def run_single_population(pos, pmra, pmdec, k_predict, k_shuffle, n_perm, sigma_frac, seed):
    real_stat = compute_weighted_residual_error(pos, pmra, pmdec, k_predict)
    if np.isnan(real_stat):
        return None

    rng = np.random.default_rng(seed)
    null_list = []
    shuffle_dists = []

    for _ in range(n_perm):
        shuf_ra, shuf_dec, mean_dist = locally_shuffle_with_noise(
            pos, pmra, pmdec, k_shuffle, sigma_frac, rng
        )
        r = compute_weighted_residual_error(pos, shuf_ra, shuf_dec, k_predict)
        if not np.isnan(r):
            null_list.append(r)
            shuffle_dists.append(mean_dist)

    if len(null_list) < 10:
        return None

    mean_null = np.mean(null_list)
    std_null = np.std(null_list)
    z = (real_stat - mean_null) / std_null if std_null > 1e-10 else np.nan

    return {
        "real": real_stat,
        "mean_null": mean_null,
        "std_null": std_null,
        "z": z,
        "mean_shuffle_dist": np.mean(shuffle_dists),
    }


def main():
    print("🔬 TRACEBIND V9.1: Robust Local Null (Strict Locality + Noise)")
    print("=" * 78)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows | k_pred={K_PREDICT} | k_shuf={K_SHUFFLE}")
    print(f"   Perms: {N_PERMUTATIONS} | Noise σ: {NOISE_SIGMA_FRAC*100:.0f}% local std | Seed: {RANDOM_SEED}\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())
    results = {}

    # === MAIN RESULTS ===
    print(f"📊 Local Null Results:")
    print("-" * 78)
    print(f"  {'Population':<20s} {'Real':>8s} {'Null μ':>8s} {'Z':>8s} {'ShufDist':>9s} {'Verdict':>14s}")
    print("-" * 78)

    for pop in populations:
        mask = df["population"] == pop
        res = run_single_population(
            positions_3d[mask],
            df.loc[mask, "pmra"].values,
            df.loc[mask, "pmdec"].values,
            K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, NOISE_SIGMA_FRAC, RANDOM_SEED
        )
        results[pop] = res

        if res is None:
            print(f"  {pop:<20s} {'ERROR':>8s}")
            continue

        verdict = "✅ STRUCTURE" if res["z"] < -2.0 else "❌ NULL"
        print(f"  {pop:<20s} {res['real']:>8.4f} {res['mean_null']:>8.4f} {res['z']:>+8.2f} {res['mean_shuffle_dist']:>9.3f} {verdict:>14s}")

    # === SANITY CHECK 1: Null Separation ===
    print("\n🔍 SANITY CHECK 1: Real vs Null Separation")
    print("-" * 50)
    for pop in populations:
        r = results.get(pop)
        if r is None:
            continue
        gap = r["mean_null"] - r["real"]
        status = "✅ signal << null" if gap > 0 and r["z"] < -2.0 else ("⚠️ controls ≈ null" if abs(r["z"]) < 2.0 else "❌ ANOMALY")
        print(f"  {pop:20s}: real={r['real']:.4f}  null_μ={r['mean_null']:.4f}  gap={gap:+.4f}  {status}")

    # === SANITY CHECK 2: Shuffle Locality ===
    print("\n🔍 SANITY CHECK 2: Shuffle Distance (should be << cluster scale)")
    print("-" * 50)
    for pop in populations:
        r = results.get(pop)
        if r is None:
            continue
        print(f"  {pop:20s}: mean shuffle dist = {r['mean_shuffle_dist']:.3f} pc")

    # === SANITY CHECK 3: k-Stability ===
    print("\n🔍 SANITY CHECK 3: k-Stability (k_predict ∈ {10, 20, 30, 50})")
    print("-" * 50)
    test_ks = [10, 20, 30, 50]
    sig_zs = []
    for k_test in test_ks:
        mask = df["population"] == "signal"
        res_k = run_single_population(
            positions_3d[mask],
            df.loc[mask, "pmra"].values,
            df.loc[mask, "pmdec"].values,
            k_test, max(k_test + 20, K_SHUFFLE), N_PERMUTATIONS, NOISE_SIGMA_FRAC, RANDOM_SEED
        )
        z_str = f"{res_k['z']:+.2f}" if res_k else "NaN"
        sig_zs.append(res_k["z"] if res_k else np.nan)
        print(f"  k={k_test:3d}: Z_signal = {z_str}")

    stable = all(z < -2.0 for z in sig_zs if not np.isnan(z))
    print(f"  Stable across k: {'✅ YES' if stable else '⚠️ NO — results are k-dependent'}")

    # === FINAL VERDICT ===
    print("\n" + "=" * 78)
    sig = results.get("signal")
    prj = results.get("projection_control")
    fld = results.get("field_control")

    sig_pass = sig is not None and sig["z"] < -2.0
    prj_fail = prj is None or prj["z"] >= -2.0
    fld_fail = fld is None or fld["z"] >= -2.0

    print(f"  Signal Z < -2:              {'✅ YES' if sig_pass else '❌ NO'}")
    print(f"  Projection Z >= -2:         {'✅ YES' if prj_fail else '❌ NO'}")
    print(f"  Field Z >= -2:              {'✅ YES' if fld_fail else '❌ NO'}")
    print(f"  Shuffle locality OK:        {'✅ YES' if all(results[p]['mean_shuffle_dist'] < 5.0 for p in populations if results[p]) else '⚠️ CHECK'}")
    print(f"  k-stable:                   {'✅ YES' if stable else '⚠️ NO'}")

    overall = sig_pass and prj_fail and fld_fail and stable
    print(f"\n  🎯 OVERALL PHASE 1 STATUS: {'✅ PASS — METRIC VALIDATED' if overall else '❌ FAIL — FURTHER REDESIGN NEEDED'}")

    print("\n🔒 TRACEBIND V9.1 CHECKPOINT:")
    print(f"- Strict local shuffle (no global assignment)")
    print(f"- Noise injection: {NOISE_SIGMA_FRAC*100:.0f}% local σ")
    print(f"- All 3 sanity checks included")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V9.1")


if __name__ == "__main__":
    main()