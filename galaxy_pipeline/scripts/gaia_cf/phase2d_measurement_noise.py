"""
TRACEBIND Phase 2D V2: Gaussian Observational Noise Stress Test
Tests metric robustness under independent Gaussian astrometric perturbations.
NOT a full Gaia DR3 error model (no covariance, no magnitude dependence).
Parameterized by absolute σ_plx (mas) and σ_pm (mas/yr).
Records Δratio to quantify sensitivity degradation.
License: CC0 1.0 Universal
"""
import numpy as np
import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "sim")

TEST_SIGMAS = [1.5, 15.0]
# Absolute parallax errors in mas (Gaia DR3 typical range for bright stars)
PLX_SIGMAS_MAS = [0.02, 0.05, 0.10, 0.30, 0.50]
# Absolute PM errors in mas/yr
PM_SIGMAS_MAS_YR = [0.05, 0.20, 1.00]
SEEDS = [42, 123, 999]
N_PERMUTATIONS = 200
N_STARS = 1500
K_PREDICT = 30
K_SHUFFLE = 50


# === GENERATOR FUNCTIONS (unchanged from Phase 2C V2) ===
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


# === LOCKED V11 METRIC (unchanged) ===
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


def compute_ratio_distribution(positions_3d, pmra, pmdec, k_predict, k_shuffle, n_perm, rng):
    real_err = compute_loo_prediction_error(positions_3d, pmra, pmdec, k_predict)
    if np.isnan(real_err): return np.array([])
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
            if len(nbr_idx) == 0: shuffled_pm[i] = pm_vectors[i]; continue
            chosen = rng.integers(0, len(nbr_idx))
            local_vel_std = np.std(pm_vectors[nbr_idx], axis=0)
            noise = rng.normal(0, 0.1 * local_vel_std, size=2)
            shuffled_pm[i] = pm_vectors[nbr_idx[chosen]] + noise
        err = compute_loo_prediction_error(positions_3d, shuffled_pm[:, 0], shuffled_pm[:, 1], k_predict)
        if not np.isnan(err): null_errors.append(err)
    if len(null_errors) < 10: return np.array([])
    return real_err / np.array(null_errors)


def apply_gaussian_obs_noise(ra, dec, parallax, pmra, pmdec, sigma_plx_mas, sigma_pm_mas_yr, rng):
    """
    Apply independent Gaussian noise parameterized by ABSOLUTE uncertainties.
    NOT a full Gaia error model: no covariance, no magnitude/color dependence.
    Parallax clamped >0.01 mas to prevent nonphysical distances.
    """
    noisy_plx = parallax + rng.normal(0, sigma_plx_mas, size=len(parallax))
    noisy_plx = np.maximum(noisy_plx, 0.01)
    noisy_pmra = pmra + rng.normal(0, sigma_pm_mas_yr, size=len(pmra))
    noisy_pmdec = pmdec + rng.normal(0, sigma_pm_mas_yr, size=len(pmdec))
    return ra, dec, noisy_plx, noisy_pmra, noisy_pmdec


def run_noise_condition(seed, sigma, sigma_plx, sigma_pm):
    master_rng = np.random.default_rng(seed)
    sig_data_seed = master_rng.integers(0, 2**31)
    fld_data_seed = master_rng.integers(0, 2**31)
    sig_null_clean_seed = master_rng.integers(0, 2**31)
    fld_null_clean_seed = master_rng.integers(0, 2**31)
    sig_null_noisy_seed = master_rng.integers(0, 2**31)
    fld_null_noisy_seed = master_rng.integers(0, 2**31)
    noise_seed = master_rng.integers(0, 2**31)

    rng_sig = np.random.default_rng(sig_data_seed)
    rng_fld = np.random.default_rng(fld_data_seed)
    rng_noise = np.random.default_rng(noise_seed)

    # Generate CLEAN signal
    sx, sy, sz = generate_plummer_sphere(N_STARS, rng_sig)
    svx, svy, svz = generate_convergent_velocities(N_STARS, rng_sig, sigma)
    s_ra, s_dec, s_plx, s_pmra, s_pmdec, _ = cartesian_to_astrometry(sx, sy, sz, svx, svy, svz, rng_sig)

    # Clean signal ratio
    pos_sig_clean = astrometry_to_cartesian(s_ra, s_dec, s_plx)
    sig_clean_dist = compute_ratio_distribution(
        pos_sig_clean, s_pmra, s_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS,
        np.random.default_rng(sig_null_clean_seed))
    sig_clean_median = float(np.median(sig_clean_dist)) if len(sig_clean_dist) > 0 else np.nan

    # NOISY signal
    _, _, s_plx_n, s_pmra_n, s_pmdec_n = apply_gaussian_obs_noise(
        s_ra, s_dec, s_plx, s_pmra, s_pmdec, sigma_plx, sigma_pm, rng_noise)
    pos_sig_noisy = astrometry_to_cartesian(s_ra, s_dec, s_plx_n)
    sig_noisy_dist = compute_ratio_distribution(
        pos_sig_noisy, s_pmra_n, s_pmdec_n, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS,
        np.random.default_rng(sig_null_noisy_seed))

    # Generate CLEAN field
    fa_distance = 1000.0 / s_plx
    fa_theta = np.arccos(2 * rng_fld.uniform(0, 1, N_STARS) - 1)
    fa_phi = 2 * np.pi * rng_fld.uniform(0, 1, N_STARS)
    fx = fa_distance * np.sin(fa_theta) * np.cos(fa_phi)
    fy = fa_distance * np.sin(fa_theta) * np.sin(fa_phi)
    fz = fa_distance * np.cos(fa_theta)
    fvx, fvy, fvz = generate_isotropic_velocities(N_STARS, rng_fld)
    f_ra, f_dec, f_plx, f_pmra, f_pmdec, _ = cartesian_to_astrometry(fx, fy, fz, fvx, fvy, fvz, rng_fld)

    # Clean field ratio
    pos_fld_clean = astrometry_to_cartesian(f_ra, f_dec, f_plx)
    fld_clean_dist = compute_ratio_distribution(
        pos_fld_clean, f_pmra, f_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS,
        np.random.default_rng(fld_null_clean_seed))
    fld_clean_median = float(np.median(fld_clean_dist)) if len(fld_clean_dist) > 0 else np.nan

    # NOISY field (same noise params)
    _, _, f_plx_n, f_pmra_n, f_pmdec_n = apply_gaussian_obs_noise(
        f_ra, f_dec, f_plx, f_pmra, f_pmdec, sigma_plx, sigma_pm, rng_noise)
    pos_fld_noisy = astrometry_to_cartesian(f_ra, f_dec, f_plx_n)
    fld_noisy_dist = compute_ratio_distribution(
        pos_fld_noisy, f_pmra_n, f_pmdec_n, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS,
        np.random.default_rng(fld_null_noisy_seed))

    def summarize(dist):
        if len(dist) == 0: return {"median": np.nan, "nri_low": np.nan, "nri_high": np.nan}
        return {"median": float(np.median(dist)),
                "nri_low": float(np.percentile(dist, 2.5)),
                "nri_high": float(np.percentile(dist, 97.5))}

    sig_n = summarize(sig_noisy_dist)
    fld_n = summarize(fld_noisy_dist)

    separated = sig_n["nri_high"] < fld_n["nri_low"] if not any(np.isnan([sig_n["nri_high"], fld_n["nri_low"]])) else False
    margin = fld_n["median"] - sig_n["median"] if not any(np.isnan([fld_n["median"], sig_n["median"]])) else np.nan

    # Δratio: sensitivity loss due to noise
    delta_sig = sig_n["median"] - sig_clean_median if not any(np.isnan([sig_n["median"], sig_clean_median])) else np.nan
    delta_fld = fld_n["median"] - fld_clean_median if not any(np.isnan([fld_n["median"], fld_clean_median])) else np.nan

    return {
        "sigma": sigma, "sigma_plx_mas": sigma_plx, "sigma_pm_mas_yr": sigma_pm, "seed": seed,
        "sig_clean_median": sig_clean_median, "sig_noisy_median": sig_n["median"],
        "sig_nri_high": sig_n["nri_high"], "delta_sig_ratio": delta_sig,
        "fld_clean_median": fld_clean_median, "fld_noisy_median": fld_n["median"],
        "fld_nri_low": fld_n["nri_low"], "delta_fld_ratio": delta_fld,
        "margin": margin, "separated": separated
    }


def main():
    print("🔬 TRACEBIND PHASE 2D V2: GAUSSIAN OBSERVATIONAL NOISE STRESS TEST")
    print("⚠️  NOT a full Gaia DR3 error model (no covariance, no mag/color dependence)")
    print(f"Sigmas: {TEST_SIGMAS} | σ_plx: {PLX_SIGMAS_MAS} mas | σ_pm: {PM_SIGMAS_MAS_YR} mas/yr")
    print(f"Seeds: {SEEDS} | Perms: {N_PERMUTATIONS}")
    print("=" * 120)

    results = []
    for sigma in TEST_SIGMAS:
        print(f"\n📊 σ = {sigma:.1f} km/s")
        print("-" * 120)
        print(f"{'σplx':>6s} {'σpm':>6s} {'Seed':>5s} {'ΔSig':>7s} {'ΔFld':>7s} {'Margin':>7s} {'Sep?':>5s}")
        print("-" * 120)

        for sp in PLX_SIGMAS_MAS:
            for spm in PM_SIGMAS_MAS_YR:
                for seed in SEEDS:
                    r = run_noise_condition(seed, sigma, sp, spm)
                    results.append(r)
                    sep_str = "✅" if r["separated"] else "❌"
                    ds = f"{r['delta_sig_ratio']:+.3f}" if not np.isnan(r['delta_sig_ratio']) else "NaN"
                    df = f"{r['delta_fld_ratio']:+.3f}" if not np.isnan(r['delta_fld_ratio']) else "NaN"
                    m = f"{r['margin']:+.3f}" if not np.isnan(r['margin']) else "NaN"
                    print(f"{sp:>5.2f} {spm:>5.2f} {r['seed']:>5d} {ds:>7s} {df:>7s} {m:>7s} {sep_str:>5s}")

    df_out = pd.DataFrame(results)
    out_file = os.path.join(OUTPUT_DIR, "phase2d_v2_noise_stress_results.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_out.to_csv(out_file, index=False)

    # === DEGRADATION SYNTHESIS ===
    print("\n" + "=" * 120)
    print("📋 SENSITIVITY DEGRADATION SYNTHESIS")
    print("-" * 60)
    for sigma in TEST_SIGMAS:
        sigma_rows = [r for r in results if r["sigma"] == sigma]
        print(f"\n  σ = {sigma:.1f} km/s:")

        conditions = {}
        for r in sigma_rows:
            key = (r["sigma_plx_mas"], r["sigma_pm_mas_yr"])
            if key not in conditions: conditions[key] = []
            conditions[key].append(r)

        print(f"    {'σplx':>6s} {'σpm':>6s} {'AvgΔSig':>8s} {'WorstMargin':>12s} {'Sep':>6s}")
        print(f"    {'-'*45}")
        for (sp, spm), rows in sorted(conditions.items()):
            avg_ds = np.nanmean([r["delta_sig_ratio"] for r in rows])
            margins = [r["margin"] for r in rows if not np.isnan(r["margin"])]
            worst_m = min(margins) if margins else np.nan
            seps = sum(1 for r in rows if r["separated"])
            total = len(rows)
            status = "✅" if seps == total else ("⚠️" if seps >= total - 1 else "❌")
            ds_str = f"{avg_ds:+.3f}" if not np.isnan(avg_ds) else "NaN"
            wm_str = f"{worst_m:+.3f}" if not np.isnan(worst_m) else "NaN"
            print(f"    {sp:>5.2f} {spm:>5.2f} {ds_str:>8s} {wm_str:>12s} {seps:>3d}/{total:<3d} {status}")

        failed = [(sp, spm) for (sp, spm), rows in conditions.items()
                  if sum(1 for r in rows if r["separated"]) < len(rows) - 1]
        if failed:
            print(f"\n    ⚠️ FAILURE BOUNDARY: separation lost at σ_plx={failed[0][0]:.2f} mas, σ_pm={failed[0][1]:.2f} mas/yr")
        else:
            print(f"\n    ✅ ALL TESTED NOISE LEVELS MAINTAIN SEPARATION")

    print(f"\n💾 Saved to {out_file}")
    print("\n🔒 PHASE 2D V2 CHECKPOINT:")
    print("- Noise model: Independent Gaussian (NOT full Gaia DR3)")
    print("- Parameterization: Absolute σ_plx (mas), σ_pm (mas/yr)")
    print("- Records Δratio for sensitivity degradation curve")
    print("- Distance inversion bias acknowledged (E[1/X] ≠ 1/E[X])")
    print("- Status: GAUSSIAN OBSERVATIONAL NOISE STRESS MAPPED")


if __name__ == "__main__":
    main()