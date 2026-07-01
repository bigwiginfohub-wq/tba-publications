"""
TRACEBIND Phase 2C V2: Statistical Separation Audit
Measures distributional separation between signal and control ratio distributions.
Tests σ=1.5 (strongest) and σ=15.0 (weakest discrimination).
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
SEEDS = [1, 42, 123, 999]
N_PERMUTATIONS = 200
N_STARS = 1500
K_PREDICT = 30
K_SHUFFLE = 50
THRESHOLD = 0.80


# === GENERATOR FUNCTIONS (identical to sweep V2) ===
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
    """Returns full ratio distribution: real_err / each_null_err."""
    real_err = compute_loo_prediction_error(positions_3d, pmra, pmdec, k_predict)
    if np.isnan(real_err):
        return np.array([])

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
        if not np.isnan(err):
            null_errors.append(err)

    if len(null_errors) < 10:
        return np.array([])

    return real_err / np.array(null_errors)


def summarize_distribution(dist, name):
    """Summarize ratio distribution with CORRECT terminology."""
    if len(dist) == 0:
        return {"pop": name, "median": np.nan, "nri_low": np.nan, "nri_high": np.nan,
                "pct_below_thresh": np.nan}
    return {
        "pop": name,
        "median": float(np.median(dist)),
        # RENAMED: Null-Ratio Interval, NOT confidence interval
        "nri_low": float(np.percentile(dist, 2.5)),
        "nri_high": float(np.percentile(dist, 97.5)),
        "pct_below_thresh": float(np.mean(dist < THRESHOLD) * 100),
    }


def run_seed_sigma(seed, sigma):
    master_rng = np.random.default_rng(seed)

    # Independent child seeds for each component
    sig_data_seed = master_rng.integers(0, 2**31)
    fld_data_seed = master_rng.integers(0, 2**31)
    prj_data_seed = master_rng.integers(0, 2**31)
    # INDEPENDENT null RNGs per population (fixes correlation issue)
    sig_null_seed = master_rng.integers(0, 2**31)
    fld_null_seed = master_rng.integers(0, 2**31)
    prj_null_seed = master_rng.integers(0, 2**31)

    rng_sig_data = np.random.default_rng(sig_data_seed)
    rng_fld_data = np.random.default_rng(fld_data_seed)
    rng_prj_data = np.random.default_rng(prj_data_seed)
    rng_sig_null = np.random.default_rng(sig_null_seed)
    rng_fld_null = np.random.default_rng(fld_null_seed)
    rng_prj_null = np.random.default_rng(prj_null_seed)

    # === SIGNAL ===
    sx, sy, sz = generate_plummer_sphere(N_STARS, rng_sig_data)
    svx, svy, svz = generate_convergent_velocities(N_STARS, rng_sig_data, sigma)
    s_ra, s_dec, s_plx, s_pmra, s_pmdec, _ = cartesian_to_astrometry(sx, sy, sz, svx, svy, svz, rng_sig_data)
    pos_sig = astrometry_to_cartesian(s_ra, s_dec, s_plx)
    sig_dist = compute_ratio_distribution(pos_sig, s_pmra, s_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_sig_null)

    # === FIELD ===
    fa_distance = 1000.0 / s_plx
    fa_theta = np.arccos(2 * rng_fld_data.uniform(0, 1, N_STARS) - 1)
    fa_phi = 2 * np.pi * rng_fld_data.uniform(0, 1, N_STARS)
    fx = fa_distance * np.sin(fa_theta) * np.cos(fa_phi)
    fy = fa_distance * np.sin(fa_theta) * np.sin(fa_phi)
    fz = fa_distance * np.cos(fa_theta)
    fvx, fvy, fvz = generate_isotropic_velocities(N_STARS, rng_fld_data)
    f_ra, f_dec, f_plx, f_pmra, f_pmdec, _ = cartesian_to_astrometry(fx, fy, fz, fvx, fvy, fvz, rng_fld_data)
    pos_fld = astrometry_to_cartesian(f_ra, f_dec, f_plx)
    fld_dist = compute_ratio_distribution(pos_fld, f_pmra, f_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_fld_null)

    # === PROJECTION (V2.0) ===
    shuffle_idx = rng_prj_data.permutation(N_STARS)
    b_ra, b_dec, b_plx = s_ra[shuffle_idx], s_dec[shuffle_idx], s_plx
    orig_speeds = np.sqrt(s_pmra[shuffle_idx]**2 + s_pmdec[shuffle_idx]**2)
    rand_theta = np.arccos(2 * rng_prj_data.uniform(0, 1, N_STARS) - 1)
    rand_phi = 2 * np.pi * rng_prj_data.uniform(0, 1, N_STARS)
    b_pmra = orig_speeds * np.sin(rand_theta) * np.cos(rand_phi)
    b_pmdec = orig_speeds * np.sin(rand_theta) * np.sin(rand_phi)
    pos_prj = astrometry_to_cartesian(b_ra, b_dec, b_plx)
    prj_dist = compute_ratio_distribution(pos_prj, b_pmra, b_pmdec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_prj_null)

    sig_sum = summarize_distribution(sig_dist, "signal")
    fld_sum = summarize_distribution(fld_dist, "field")
    prj_sum = summarize_distribution(prj_dist, "projection")

    # EFFECT MARGIN: control_median - signal_median
    margin_fld = fld_sum["median"] - sig_sum["median"] if not (np.isnan(fld_sum["median"]) or np.isnan(sig_sum["median"])) else np.nan
    margin_prj = prj_sum["median"] - sig_sum["median"] if not (np.isnan(prj_sum["median"]) or np.isnan(sig_sum["median"])) else np.nan

    # DISTRIBUTIONAL SEPARATION: signal upper < control lower
    sep_fld = sig_sum["nri_high"] < fld_sum["nri_low"] if not any(np.isnan([sig_sum["nri_high"], fld_sum["nri_low"]])) else False
    sep_prj = sig_sum["nri_high"] < prj_sum["nri_low"] if not any(np.isnan([sig_sum["nri_high"], prj_sum["nri_low"]])) else False

    return {
        "seed": seed, "sigma": sigma,
        "signal": sig_sum, "field": fld_sum, "projection": prj_sum,
        "margin_field": margin_fld, "margin_projection": margin_prj,
        "separated_field": sep_fld, "separated_projection": sep_prj,
    }


def main():
    print("🔬 TRACEBIND PHASE 2C V2: STATISTICAL SEPARATION AUDIT")
    print(f"Sigmas: {TEST_SIGMAS} | Seeds: {SEEDS} | Perms: {N_PERMUTATIONS} | Threshold: {THRESHOLD}")
    print("=" * 105)

    all_results = []
    for sigma in TEST_SIGMAS:
        print(f"\n📊 σ = {sigma:.1f} km/s")
        print("-" * 105)
        print(f"{'Seed':>5s} {'Pop':>10s} {'Median':>7s} {'95% NRI':>18s} {'%<0.80':>7s} {'Margin':>7s} {'Sep?':>5s}")
        print("-" * 105)

        for seed in SEEDS:
            r = run_seed_sigma(seed, sigma)
            all_results.append(r)

            for pop_key in ["signal", "field", "projection"]:
                p = r[pop_key]
                nri_str = f"[{p['nri_low']:.3f},{p['nri_high']:.3f}]"

                if pop_key == "signal":
                    margin_str = ""
                    sep_str = ""
                    verdict = "✅ DETECT" if p['nri_high'] < THRESHOLD else ("⚠️ WEAK" if p['median'] < THRESHOLD else "❌ MISS")
                else:
                    margin = r[f"margin_{pop_key}"]
                    separated = r[f"separated_{pop_key}"]
                    margin_str = f"{margin:+.3f}" if not np.isnan(margin) else "NaN"
                    sep_str = "✅" if separated else "❌"
                    overlap = p['nri_low'] < THRESHOLD
                    pct = p['pct_below_thresh']
                    if separated and pct < 5:
                        verdict = "✅ SAFE"
                    elif not overlap and pct < 10:
                        verdict = "⚠️ CLOSE"
                    else:
                        verdict = "❌ OVERLAP"

                print(f"{r['seed']:>5d} {p['pop']:>10s} {p['median']:>7.3f} {nri_str:>18s} {p['pct_below_thresh']:>6.1f}% {margin_str:>7s} {sep_str:>5s} {verdict}")

    # Save full results
    rows = []
    for r in all_results:
        for pop_key in ["signal", "field", "projection"]:
            p = r[pop_key]
            rows.append({
                "sigma": r["sigma"], "seed": r["seed"], "population": pop_key,
                "median": p["median"], "nri_low": p["nri_low"], "nri_high": p["nri_high"],
                "pct_below_threshold": p["pct_below_thresh"],
                "effect_margin": r.get(f"margin_{pop_key}", np.nan),
                "distributions_separated": r.get(f"separated_{pop_key}", None),
            })

    df = pd.DataFrame(rows)
    out_file = os.path.join(OUTPUT_DIR, "phase2c_v2_separation_results.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(out_file, index=False)

    # === FINAL SYNTHESIS ===
    print("\n" + "=" * 105)
    print("📋 SEPARATION SYNTHESIS")
    print("-" * 50)
    for sigma in TEST_SIGMAS:
        sigma_results = [r for r in all_results if r["sigma"] == sigma]

        sig_medians = [r["signal"]["median"] for r in sigma_results]
        fld_margins = [r["margin_field"] for r in sigma_results if not np.isnan(r["margin_field"])]
        prj_margins = [r["margin_projection"] for r in sigma_results if not np.isnan(r["margin_projection"])]
        fld_seps = sum(1 for r in sigma_results if r["separated_field"])
        prj_seps = sum(1 for r in sigma_results if r["separated_projection"])

        print(f"\n  σ = {sigma:.1f} km/s:")
        print(f"    Signal median range:     [{min(sig_medians):.3f}, {max(sig_medians):.3f}]")
        print(f"    Field effect margin:     [{min(fld_margins):+.3f}, {max(fld_margins):+.3f}]" if fld_margins else "    Field margin: NaN")
        print(f"    Projection effect margin:[{min(prj_margins):+.3f}, {max(prj_margins):+.3f}]" if prj_margins else "    Projection margin: NaN")
        print(f"    Field separated:         {fld_seps}/{len(sigma_results)} seeds")
        print(f"    Projection separated:    {prj_seps}/{len(sigma_results)} seeds")

        if fld_seps == len(sigma_results) and prj_seps == len(sigma_results):
            print(f"    → ✅ FULLY SEPARATED at this σ")
        elif fld_seps >= len(sigma_results) - 1 and prj_seps >= len(sigma_results) - 1:
            print(f"    → ⚠️ ACCEPTABLE (1 seed marginal)")
        else:
            print(f"    → ❌ INSUFFICIENT SEPARATION")

    print(f"\n💾 Saved to {out_file}")
    print("\n🔒 PHASE 2C V2 CHECKPOINT:")
    print("- Metric: 95% Null-Ratio Interval (NOT confidence interval)")
    print("- Separation: signal NRI upper < control NRI lower")
    print("- Effect margin: control_median - signal_median")
    print("- Independent null RNGs per population")
    print("- Status: DISTRIBUTIONAL SEPARATION AUDITED")


if __name__ == "__main__":
    main()