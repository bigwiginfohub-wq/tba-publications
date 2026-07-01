"""
TRACEBIND Phase 3A V4: Kinematic Contamination Test (Publication-Grade)
Targeted MC sampling: 3 seeds full grid, 50 seeds at 70% purity boundary.
Wilson CI for binomial success rate. Independent null RNG streams.
No qualitative labels at boundary; raw rates reported.
License: CC0 1.0 Universal
"""
import numpy as np
import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors
from statsmodels.stats.proportion import proportion_confint

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "sim")

PURITIES = [1.00, 0.90, 0.80, 0.70]
TEST_SIGMAS = [1.5, 15.0]
SEEDS_FULL = [42, 123, 999]
SEEDS_BOUNDARY = list(range(50))
N_PERMUTATIONS = 200
N_STARS = 1500
K_PREDICT = 30
K_SHUFFLE = 50


# === GENERATOR & METRIC FUNCTIONS (unchanged from V3) ===
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

def create_kinematic_contamination(sig_pmra, sig_pmdec, fld_pmra, fld_pmdec, purity, rng):
    n_total = len(sig_pmra)
    n_contam = int(round((1.0 - purity) * n_total))
    if n_contam == 0:
        return sig_pmra.copy(), sig_pmdec.copy()
    replace_idx = rng.choice(n_total, size=n_contam, replace=False)
    field_idx = rng.choice(len(fld_pmra), size=n_contam, replace=False)
    mixed_pmra = sig_pmra.copy()
    mixed_pmdec = sig_pmdec.copy()
    mixed_pmra[replace_idx] = fld_pmra[field_idx]
    mixed_pmdec[replace_idx] = fld_pmdec[field_idx]
    return mixed_pmra, mixed_pmdec


def run_purity_condition(seed, sigma, purity):
    """Single realization with INDEPENDENT null RNG streams."""
    master_rng = np.random.default_rng(seed)

    # Independent seeds for each stochastic component
    sig_data_seed = master_rng.integers(0, 2**31)
    fld_data_seed = master_rng.integers(0, 2**31)
    mix_seed      = master_rng.integers(0, 2**31)
    pure_null_seed = master_rng.integers(0, 2**31)   # FIX: independent stream
    mix_null_seed  = master_rng.integers(0, 2**31)   # FIX: independent stream
    fld_null_seed  = master_rng.integers(0, 2**31)   # FIX: independent stream

    rng_sig = np.random.default_rng(sig_data_seed)
    rng_fld = np.random.default_rng(fld_data_seed)
    rng_mix = np.random.default_rng(mix_seed)
    rng_pure_null = np.random.default_rng(pure_null_seed)
    rng_mix_null  = np.random.default_rng(mix_null_seed)
    rng_fld_null  = np.random.default_rng(fld_null_seed)

    # Generate pure signal
    sx, sy, sz = generate_plummer_sphere(N_STARS, rng_sig)
    svx, svy, svz = generate_convergent_velocities(N_STARS, rng_sig, sigma)
    s_ra, s_dec, s_plx, s_pmra, s_pmdec, _ = cartesian_to_astrometry(sx, sy, sz, svx, svy, svz, rng_sig)

    # Generate pure field
    fa_distance = 1000.0 / s_plx
    fa_theta = np.arccos(2 * rng_fld.uniform(0, 1, N_STARS) - 1)
    fa_phi = 2 * np.pi * rng_fld.uniform(0, 1, N_STARS)
    fx = fa_distance * np.sin(fa_theta) * np.cos(fa_phi)
    fy = fa_distance * np.sin(fa_theta) * np.sin(fa_phi)
    fz = fa_distance * np.cos(fa_theta)
    fvx, fvy, fvz = generate_isotropic_velocities(N_STARS, rng_fld)
    f_ra, f_dec, f_plx, f_pmra, f_pmdec, _ = cartesian_to_astrometry(fx, fy, fz, fvx, fvy, fvz, rng_fld)

    # Pure signal ratio (independent null stream)
    pos_sig = astrometry_to_cartesian(s_ra, s_dec, s_plx)
    pure_dist = compute_ratio_distribution(pos_sig, s_pmra, s_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_pure_null)
    pure_median = float(np.median(pure_dist)) if len(pure_dist) > 0 else np.nan

    # Kinematic contamination
    m_pmra, m_pmdec = create_kinematic_contamination(s_pmra, s_pmdec, f_pmra, f_pmdec, purity, rng_mix)
    pos_mix = astrometry_to_cartesian(s_ra, s_dec, s_plx)
    mix_dist = compute_ratio_distribution(pos_mix, m_pmra, m_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_mix_null)

    # Field ratio (independent null stream)
    pos_fld = astrometry_to_cartesian(f_ra, f_dec, f_plx)
    fld_dist = compute_ratio_distribution(pos_fld, f_pmra, f_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_fld_null)

    def summarize(dist):
        if len(dist) == 0: return {"median": np.nan, "nri_low": np.nan, "nri_high": np.nan}
        return {"median": float(np.median(dist)),
                "nri_low": float(np.percentile(dist, 2.5)),
                "nri_high": float(np.percentile(dist, 97.5))}

    mix_s = summarize(mix_dist)
    fld_s = summarize(fld_dist)
    separated = mix_s["nri_high"] < fld_s["nri_low"] if not any(np.isnan([mix_s["nri_high"], fld_s["nri_low"]])) else False
    margin = fld_s["median"] - mix_s["median"] if not any(np.isnan([fld_s["median"], mix_s["median"]])) else np.nan
    delta_median = mix_s["median"] - pure_median if not any(np.isnan([mix_s["median"], pure_median])) else np.nan

    return {
        "sigma": sigma, "purity": purity, "seed": seed,
        "pure_median": pure_median, "mix_median": mix_s["median"],
        "delta_median": delta_median, "mix_nri_high": mix_s["nri_high"],
        "fld_median": fld_s["median"], "fld_nri_low": fld_s["nri_low"],
        "margin": margin, "separated": separated
    }


def main():
    print("🔬 TRACEBIND PHASE 3A V4: KINEMATIC CONTAMINATION (PUBLICATION-GRADE)")
    print(f"Full grid: {len(SEEDS_FULL)} seeds | Boundary (70%): {len(SEEDS_BOUNDARY)} seeds")
    print("=" * 115)

    results = []
    for sigma in TEST_SIGMAS:
        print(f"\n📊 σ = {sigma:.1f} km/s")
        print("-" * 115)

        for purity in PURITIES:
            seeds_to_use = SEEDS_BOUNDARY if purity == 0.70 else SEEDS_FULL
            label = "BOUNDARY" if purity == 0.70 else "FULL"

            print(f"\n  Purity={purity:.0%} ({label}, n={len(seeds_to_use)}):")
            print(f"  {'Seed':>5s} {'MixMed':>7s} {'ΔMed':>7s} {'Margin':>7s} {'Sep?':>5s}")
            print(f"  {'-'*35}")

            for seed in seeds_to_use:
                r = run_purity_condition(seed, sigma, purity)
                results.append(r)
                sep_str = "✅" if r["separated"] else "❌"
                dm_str = f"{r['delta_median']:+.3f}" if not np.isnan(r['delta_median']) else "NaN"
                m_str = f"{r['margin']:+.3f}" if not np.isnan(r['margin']) else "NaN"
                if purity == 0.70 and len(seeds_to_use) > 7:
                    if seed < 5 or seed >= len(seeds_to_use) - 2:
                        print(f"  {r['seed']:>5d} {r['mix_median']:>7.3f} {dm_str:>7s} {m_str:>7s} {sep_str:>5s}")
                    elif seed == 5:
                        print(f"  {'...':>5s} {'...':>7s} {'...':>7s} {'...':>7s} {'...':>5s}")
                else:
                    print(f"  {r['seed']:>5d} {r['mix_median']:>7.3f} {dm_str:>7s} {m_str:>7s} {sep_str:>5s}")

    df_out = pd.DataFrame(results)
    out_file = os.path.join(OUTPUT_DIR, "phase3a_v4_contamination_results.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_out.to_csv(out_file, index=False)

    # === PUBLICATION-GRADE SYNTHESIS ===
    print("\n" + "=" * 115)
    print("📋 QUANTITATIVE DEGRADATION SYNTHESIS (WITH WILSON CI)")
    print("-" * 80)

    for sigma in TEST_SIGMAS:
        sigma_rows = [r for r in results if r["sigma"] == sigma]
        print(f"\n  σ = {sigma:.1f} km/s:")
        print(f"    {'Purity':>7s} {'N':>4s} {'Separated':>10s} {'Rate':>7s} {'95% Wilson CI':>16s} {'AvgMargin':>10s}")
        print(f"    {'-'*65}")

        for purity in PURITIES:
            p_rows = [r for r in sigma_rows if r["purity"] == purity]
            n_total = len(p_rows)
            n_sep = sum(1 for r in p_rows if r["separated"])
            rate = n_sep / n_total if n_total > 0 else 0.0

            # Wilson confidence interval
            if n_total > 0:
                ci_low, ci_high = proportion_confint(n_sep, n_total, alpha=0.05, method="wilson")
                ci_str = f"[{ci_low:.0%}, {ci_high:.0%}]"
            else:
                ci_str = "N/A"

            margins = [r["margin"] for r in p_rows if not np.isnan(r["margin"])]
            avg_m = np.mean(margins) if margins else np.nan
            am_str = f"{avg_m:+.3f}" if not np.isnan(avg_m) else "NaN"

            print(f"    {purity:>6.0%} {n_total:>4d} {n_sep:>4d}/{n_total:<4d} {rate:>6.0%} {ci_str:>16s} {am_str:>10s}")

        # Publication-ready boundary statement (NO qualitative label)
        p70_rows = [r for r in sigma_rows if r["purity"] == 0.70]
        n70 = len(p70_rows)
        sep70 = sum(1 for r in p70_rows if r["separated"])
        rate70 = sep70 / n70 if n70 > 0 else 0.0
        ci70_low, ci70_high = proportion_confint(sep70, n70, alpha=0.05, method="wilson") if n70 > 0 else (0, 0)

        print(f"\n    📝 At 70% purity: {sep70}/{n70} separated ({rate70:.0%}, 95% CI [{ci70_low:.0%}, {ci70_high:.0%}])")

    print(f"\n💾 Saved to {out_file}")
    print("\n🔒 PHASE 3A V4 CHECKPOINT:")
    print(f"- Full grid: {len(SEEDS_FULL)} seeds | Boundary (70%): {len(SEEDS_BOUNDARY)} seeds")
    print("- Wilson 95% CI for all binomial success rates")
    print("- Independent null RNG streams (pure / mixed / field)")
    print("- No qualitative labels at boundary; raw rates + CI only")
    print("- Status: PUBLICATION-GRADE KINEMATIC CONTAMINATION VALIDATION COMPLETE")


if __name__ == "__main__":
    main()