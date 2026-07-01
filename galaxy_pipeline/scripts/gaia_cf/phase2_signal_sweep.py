"""
TRACEBIND Phase 2: Signal Strength Sweep (V2 - Corrected)
Maps detection boundary of locked V11 metric under ideal conditions.
Restores projection control, uses deterministic RNG, expands sigma grid.
Generator: V2.0 (matches Phase 1 lock; parallax shuffle NOT applied).
License: CC0 1.0 Universal
"""
import numpy as np
import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "sim")

# Expanded grid for finer boundary detection
SIGMAS_KM_S = [1.5, 3.0, 5.0, 7.5, 10.0, 15.0]
N_STARS = 1500
K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 50
RANDOM_SEED = 42


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
    vx = rng.normal(vx_mean, sigma_km_s, n)
    vy = rng.normal(vy_mean, sigma_km_s, n)
    vz = rng.normal(vz_mean, sigma_km_s, n)
    return vx, vy, vz


def generate_isotropic_velocities(n, rng, speed_mean=50.0, sigma=15.0):
    speed = np.abs(rng.normal(speed_mean, sigma, n))
    theta = np.arccos(2 * rng.uniform(0, 1, n) - 1)
    phi = 2 * np.pi * rng.uniform(0, 1, n)
    vx = speed * np.sin(theta) * np.cos(phi)
    vy = speed * np.sin(theta) * np.sin(phi)
    vz = speed * np.cos(theta)
    return vx, vy, vz


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
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def compute_loo_prediction_error(positions_3d, pmra, pmdec, k):
    """Locked V11 LOO predictor - unchanged from Phase 1."""
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2:
        return np.nan
    pm_vectors = np.column_stack([pmra, pmdec])
    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)
    dist_nbrs = distances[:, 1:]
    idx_nbrs = indices[:, 1:]
    eps = 1e-6
    weights = 1.0 / (dist_nbrs**2 + eps)
    w_norm = weights / np.sum(weights, axis=1, keepdims=True)
    vel_nbrs = pm_vectors[idx_nbrs]
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)
    errors = np.linalg.norm(pm_vectors - predicted, axis=1)
    return float(np.median(errors))


def compute_own_geometry_baseline(positions_3d, pmra, pmdec, k_predict, k_shuffle, n_perm, rng):
    """Locked V11 per-pop local-shuffle baseline - unchanged from Phase 1."""
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


def run_single_sigma(sigma_km_s, master_rng):
    """
    Generate one sweep point with ALL THREE populations.
    Uses independent child RNGs seeded deterministically from master.
    """
    # Deterministic child seeds for reproducibility without global state
    sig_seed = master_rng.integers(0, 2**31)
    fld_seed = master_rng.integers(0, 2**31)
    prj_seed = master_rng.integers(0, 2**31)
    
    rng_sig = np.random.default_rng(sig_seed)
    rng_fld = np.random.default_rng(fld_seed)
    rng_prj = np.random.default_rng(prj_seed)
    rng_null = np.random.default_rng(master_rng.integers(0, 2**31))

    # === SIGNAL ===
    sx, sy, sz = generate_plummer_sphere(N_STARS, rng_sig)
    svx, svy, svz = generate_convergent_velocities(N_STARS, rng_sig, sigma_km_s)
    s_ra, s_dec, s_plx, s_pmra, s_pmdec, _ = cartesian_to_astrometry(sx, sy, sz, svx, svy, svz, rng_sig)
    pos_sig = astrometry_to_cartesian(s_ra, s_dec, s_plx)
    sig_err = compute_loo_prediction_error(pos_sig, s_pmra, s_pmdec, K_PREDICT)
    sig_base = compute_own_geometry_baseline(pos_sig, s_pmra, s_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_null)
    sig_ratio = sig_err / sig_base if sig_base > 1e-10 else np.nan

    # === FIELD CONTROL (isotropic velocities, matched distances) ===
    fa_distance = 1000.0 / s_plx  # reuse signal parallaxes for matched distribution
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

    # === PROJECTION CONTROL (V2.0: shuffled RA/Dec only, isotropic PM directions) ===
    shuffle_idx = rng_prj.permutation(N_STARS)
    b_ra = s_ra[shuffle_idx]
    b_dec = s_dec[shuffle_idx]
    b_plx = s_plx  # V2.0: parallax NOT shuffled (matches Phase 1 lock)
    orig_speeds = np.sqrt(s_pmra[shuffle_idx]**2 + s_pmdec[shuffle_idx]**2)
    rand_theta = np.arccos(2 * rng_prj.uniform(0, 1, N_STARS) - 1)
    rand_phi = 2 * np.pi * rng_prj.uniform(0, 1, N_STARS)
    b_pmra = orig_speeds * np.sin(rand_theta) * np.cos(rand_phi)
    b_pmdec = orig_speeds * np.sin(rand_theta) * np.sin(rand_phi)
    pos_prj = astrometry_to_cartesian(b_ra, b_dec, b_plx)
    prj_err = compute_loo_prediction_error(pos_prj, b_pmra, b_pmdec, K_PREDICT)
    prj_base = compute_own_geometry_baseline(pos_prj, b_pmra, b_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_null)
    prj_ratio = prj_err / prj_base if prj_base > 1e-10 else np.nan

    return sig_ratio, prj_ratio, fld_ratio


def main():
    print("🔬 TRACEBIND PHASE 2: SIGNAL STRENGTH SWEEP (V2)")
    print("=" * 88)
    print(f"Sigmas: {SIGMAS_KM_S} km/s | k_pred={K_PREDICT} | k_shuf={K_SHUFFLE}")
    print(f"Perms: {N_PERMUTATIONS} | Seed: {RANDOM_SEED} | Generator: V2.0\n")

    master_rng = np.random.default_rng(RANDOM_SEED)
    results = []

    print(f"{'σ (km/s)':>10s} {'Sig Ratio':>10s} {'Prj Ratio':>10s} {'Fld Ratio':>10s} {'Order OK?':>10s}")
    print("-" * 58)

    for sigma in SIGMAS_KM_S:
        sig_r, prj_r, fld_r = run_single_sigma(sigma, master_rng)
        
        # Check Phase 1 ordering invariant: signal < projection AND signal < field
        order_ok = (sig_r < prj_r) and (sig_r < fld_r) if not any(np.isnan([sig_r, prj_r, fld_r])) else False
        status = "✅" if order_ok else "❌"
        
        print(f"{sigma:>10.1f} {sig_r:>10.4f} {prj_r:>10.4f} {fld_r:>10.4f} {status:>10s}")
        results.append({
            "sigma_km_s": sigma,
            "signal_ratio": sig_r,
            "projection_ratio": prj_r,
            "field_ratio": fld_r,
            "order_preserved": order_ok,
            "detectable": sig_r < 0.80 and order_ok
        })

    df_results = pd.DataFrame(results)
    out_file = os.path.join(OUTPUT_DIR, "phase2_signal_sweep_v2_results.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_results.to_csv(out_file, index=False)

    # Detection boundary summary
    detectable = [r["sigma_km_s"] for r in results if r["detectable"]]
    undetectable = [r["sigma_km_s"] for r in results if not r["detectable"]]

    print("\n" + "=" * 88)
    print("📊 DETECTION BOUNDARY SUMMARY")
    print("-" * 40)
    if detectable and undetectable:
        last_det = max(detectable)
        first_undet = min(undetectable)
        print(f"  Last detectable σ:    {last_det:.1f} km/s")
        print(f"  First undetectable σ: {first_undet:.1f} km/s")
        print(f"  → Boundary: ({last_det:.1f}, {first_undet:.1f}) km/s")
    elif all(r["detectable"] for r in results):
        print("  ✅ All tested σ values detectable with correct ordering")
    else:
        print("  ❌ No σ values satisfy both detection threshold AND ordering invariant")

    # Ordering violation check
    violations = [r["sigma_km_s"] for r in results if not r["order_preserved"]]
    if violations:
        print(f"\n  ⚠️ ORDERING VIOLATIONS at σ = {violations}")
        print("     Phase 1 invariant broken; these points are INVALID regardless of ratio.")

    print(f"\n💾 Saved to {out_file}")
    print("\n🔒 PHASE 2 SWEEP V2 CHECKPOINT:")
    print("- Metric: Locked V11 LOO (unchanged)")
    print("- Generator: V2.0 (parallax NOT shuffled, matches Phase 1)")
    print("- Populations: signal + projection + field (adversarial null restored)")
    print("- RNG: Deterministic default_rng (no global state)")
    print("- Acceptance: ratio < 0.80 AND signal < controls")
    print("- Status: SENSITIVITY CURVE MAPPED WITH REGRESSION GUARD")


if __name__ == "__main__":
    main()