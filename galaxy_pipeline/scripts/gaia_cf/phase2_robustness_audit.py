"""
TRACEBIND Phase 2: Robustness Audit at σ=1.5 km/s
Tests field control stability across multiple seeds with 200 permutations.
Converts marginal pass (margin=0.0114) into statistically defensible result.
License: CC0 1.0 Universal
"""
import numpy as np
import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "sim")

TEST_SIGMA = 1.5
SEEDS = [1, 42, 123, 999]
N_PERMUTATIONS = 200  # Increased from 50 for tighter null distribution
N_STARS = 1500
K_PREDICT = 30
K_SHUFFLE = 50


def generate_plummer_sphere(n, rng, scale_radius=2.0):
    r = scale_radius / np.sqrt(rng.uniform(0, 1, n)**(-2/3) - 1)
    theta = np.arccos(2 * rng.uniform(0, 1, n) - 1)
    phi = 2 * np.pi * rng.uniform(0, 1, n)
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z


def generate_convergent_velocities(n, rng, sigma_km_s):
    vx_mean, vy_mean, vz_mean = 30.0, -45.0, -10.0
    return (rng.normal(vx_mean, sigma_km_s, n),
            rng.normal(vy_mean, sigma_km_s, n),
            rng.normal(vz_mean, sigma_km_s, n))


def generate_isotropic_velocities(n, rng, speed_mean=50.0, sigma=15.0):
    speed = np.abs(rng.normal(speed_mean, sigma, n))
    theta = np.arccos(2 * rng.uniform(0, 1, n) - 1)
    phi = 2 * np.pi * rng.uniform(0, 1, n)
    return (speed * np.sin(theta) * np.cos(phi),
            speed * np.sin(theta) * np.sin(phi),
            speed * np.cos(theta))


def cartesian_to_astrometry(x, y, z, vx, vy, vz, rng):
    distance = np.sqrt(x**2 + y**2 + z**2)
    parallax = 1000.0 / distance
    ra = np.degrees(np.arctan2(y, x)) % 360
    dec = np.degrees(np.arcsin(z / distance))
    k = 4.74047
    pmra = k * (-vx * np.sin(np.radians(ra)) + vy * np.cos(np.radians(ra))) / distance
    pmdec = k * (-vx * np.cos(np.radians(ra)) * np.sin(np.radians(dec))
                 - vy * np.sin(np.radians(ra)) * np.sin(np.radians(dec))
                 + vz * np.cos(np.radians(dec))) / distance
    g_mag = 5 * np.log10(distance) + 2.0 + rng.normal(0, 0.3, len(distance))
    return ra, dec, parallax, pmra, pmdec, g_mag


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad, dec_rad = np.radians(ra), np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def compute_loo_prediction_error(positions_3d, pmra, pmdec, k):
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2: return np.nan
    pm_vectors = np.column_stack([pmra, pmdec])
    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)
    dist_nbrs, idx_nbrs = distances[:, 1:], indices[:, 1:]
    eps = 1e-6
    weights = 1.0 / (dist_nbrs**2 + eps)
    w_norm = weights / np.sum(weights, axis=1, keepdims=True)
    vel_nbrs = pm_vectors[idx_nbrs]
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)
    errors = np.linalg.norm(pm_vectors - predicted, axis=1)
    return float(np.median(errors))


def compute_own_geometry_baseline(positions_3d, pmra, pmdec, k_predict, k_shuffle, n_perm, rng):
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
            nbr_idx = indices_all[i, 1:safe_k_shuf]
            if len(nbr_idx) == 0:
                shuffled_pm[i] = pm_vectors[i]; continue
            chosen = rng.integers(0, len(nbr_idx))
            local_vel_std = np.std(pm_vectors[nbr_idx], axis=0)
            noise = rng.normal(0, 0.1 * local_vel_std, size=2)
            shuffled_pm[i] = pm_vectors[nbr_idx[chosen]] + noise
        err = compute_loo_prediction_error(positions_3d, shuffled_pm[:, 0], shuffled_pm[:, 1], k_predict)
        if not np.isnan(err): null_errors.append(err)
    return float(np.mean(null_errors)) if null_errors else np.nan


def run_single_seed(seed):
    master_rng = np.random.default_rng(seed)
    sig_seed = master_rng.integers(0, 2**31)
    fld_seed = master_rng.integers(0, 2**31)
    prj_seed = master_rng.integers(0, 2**31)
    null_seed = master_rng.integers(0, 2**31)

    rng_sig = np.random.default_rng(sig_seed)
    rng_fld = np.random.default_rng(fld_seed)
    rng_prj = np.random.default_rng(prj_seed)
    rng_null = np.random.default_rng(null_seed)

    # Signal
    sx, sy, sz = generate_plummer_sphere(N_STARS, rng_sig)
    svx, svy, svz = generate_convergent_velocities(N_STARS, rng_sig, TEST_SIGMA)
    s_ra, s_dec, s_plx, s_pmra, s_pmdec, _ = cartesian_to_astrometry(sx, sy, sz, svx, svy, svz, rng_sig)
    pos_sig = astrometry_to_cartesian(s_ra, s_dec, s_plx)
    sig_err = compute_loo_prediction_error(pos_sig, s_pmra, s_pmdec, K_PREDICT)
    sig_base = compute_own_geometry_baseline(pos_sig, s_pmra, s_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_null)
    sig_ratio = sig_err / sig_base if sig_base > 1e-10 else np.nan

    # Field
    fa_distance = 1000.0 / s_plx
    fa_theta = np.arccos(2 * rng_fld.uniform(0, 1, N_STARS) - 1)
    fa_phi = 2 * np.pi * rng_fld.uniform(0, 1, N_STARS)
    fx = fa_distance * np.sin(fa_theta) * np.cos(fa_phi)
    fy = fa_distance * np.sin(fa_theta) * np.sin(fa_phi)
    fz = fa_distance * np.cos(fa_theta)
    fvx, fvy, fvz = generate_isotropic_velocities(N_STARS, rng_fld)
    f_ra, f_dec, f_plx, f_pmra, f_pmdec, _ = cartesian_to_astrometry(fx, fy, fz, fvx, fvy, fvz, rng_fld)
    pos_fld = astrometry_to_cartesian(f_ra, f_dec, f_plx)
    fld_err = compute_loo_prediction_error(pos_fld, f_pmra, f_pmdec, K_PREDICT)
    fld_base = compute_own_geometry_baseline(pos_fld, f_pmra, f_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_null)
    fld_ratio = fld_err / fld_base if fld_base > 1e-10 else np.nan

    # Projection (V2.0)
    shuffle_idx = rng_prj.permutation(N_STARS)
    b_ra, b_dec, b_plx = s_ra[shuffle_idx], s_dec[shuffle_idx], s_plx
    orig_speeds = np.sqrt(s_pmra[shuffle_idx]**2 + s_pmdec[shuffle_idx]**2)
    rand_theta = np.arccos(2 * rng_prj.uniform(0, 1, N_STARS) - 1)
    rand_phi = 2 * np.pi * rng_prj.uniform(0, 1, N_STARS)
    b_pmra = orig_speeds * np.sin(rand_theta) * np.cos(rand_phi)
    b_pmdec = orig_speeds * np.sin(rand_theta) * np.sin(rand_phi)
    pos_prj = astrometry_to_cartesian(b_ra, b_dec, b_plx)
    prj_err = compute_loo_prediction_error(pos_prj, b_pmra, b_pmdec, K_PREDICT)
    prj_base = compute_own_geometry_baseline(pos_prj, b_pmra, b_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_null)
    prj_ratio = prj_err / prj_base if prj_base > 1e-10 else np.nan

    order_ok = (sig_ratio < prj_ratio) and (sig_ratio < fld_ratio) if not any(np.isnan([sig_ratio, prj_ratio, fld_ratio])) else False
    return {"seed": seed, "signal": sig_ratio, "projection": prj_ratio, "field": fld_ratio,
            "field_margin": fld_ratio - 0.80 if not np.isnan(fld_ratio) else np.nan,
            "order_ok": order_ok}


def main():
    print("🔬 TRACEBIND PHASE 2 ROBUSTNESS AUDIT")
    print(f"σ = {TEST_SIGMA} km/s | Seeds: {SEEDS} | Permutations: {N_PERMUTATIONS}")
    print("=" * 80)

    results = []
    print(f"{'Seed':>6s} {'Signal':>8s} {'Proj':>8s} {'Field':>8s} {'Margin':>8s} {'Order':>6s}")
    print("-" * 52)

    for seed in SEEDS:
        r = run_single_seed(seed)
        results.append(r)
        margin_str = f"{r['field_margin']:+.4f}" if not np.isnan(r['field_margin']) else "NaN"
        order_str = "✅" if r["order_ok"] else "❌"
        print(f"{r['seed']:>6d} {r['signal']:>8.4f} {r['projection']:>8.4f} {r['field']:>8.4f} {margin_str:>8s} {order_str:>6s}")

    df = pd.DataFrame(results)
    out_file = os.path.join(OUTPUT_DIR, "phase2_robustness_audit_results.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(out_file, index=False)

    # Summary
    all_order_ok = all(r["order_ok"] for r in results)
    min_margin = min(r["field_margin"] for r in results if not np.isnan(r["field_margin"]))
    max_margin = max(r["field_margin"] for r in results if not np.isnan(r["field_margin"]))

    print("\n" + "=" * 80)
    print("📊 ROBUSTNESS SUMMARY")
    print("-" * 40)
    print(f"  All seeds preserve ordering: {'✅ YES' if all_order_ok else '❌ NO'}")
    print(f"  Field margin range: [{min_margin:+.4f}, {max_margin:+.4f}]")
    print(f"  Min margin above 0.80: {min_margin:+.4f}")

    if all_order_ok and min_margin > 0.02:
        print("\n  🎯 VERDICT: ROBUST — Safe to proceed to Phase 2B (Gaia realism)")
    elif all_order_ok and min_margin > 0:
        print("\n  ⚠️ VERDICT: MARGINAL — Proceed with caution; consider increasing perms further")
    else:
        print("\n  ❌ VERDICT: FAILED — Do NOT proceed to Phase 2B; fix required")

    print(f"\n💾 Saved to {out_file}")


if __name__ == "__main__":
    main()