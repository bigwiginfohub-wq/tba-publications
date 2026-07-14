"""Verify subsampling stability reproducibility across independent random seeds."""
import pandas as pd
import numpy as np
import os
from tracebind_v11_core import (
    astrometry_to_tangential_velocity,
    build_neighbor_graph,
    compute_loo_prediction_error,
    compute_own_geometry_baseline
)

# ===== CONFIGURATION =====
N_SUBSAMPLES = 500
SUBSAMPLE_FRACTION = 0.80
SEEDS = [42, 314159, 12345]
K_PREDICT = 30
K_SHUFFLE = 50
N_PERM_OBSERVED = 1000
N_PERM_SUBSAMPLE = 500
NOISE_FRACTION = 0.10

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
CLUSTERS = ["pleiades", "hyades"]


def run_tracebind(df, k, noise_frac, seed, n_permutations):
    """Run V11 with configurable permutation count."""
    df = df.dropna(subset=["ra", "dec", "parallax", "pmra", "pmdec"]).copy()
    df = df[df["parallax"] > 0].copy()
    if len(df) <= k:
        return {"real_error": np.nan, "null_mean": np.nan, "R": np.nan, "p": np.nan}

    pos_3d, vel_vec = astrometry_to_tangential_velocity(
        df["ra"].values, df["dec"].values, df["parallax"].values,
        df["pmra"].values, df["pmdec"].values
    )
    max_k = max(k, K_SHUFFLE) + 1
    graph = build_neighbor_graph(pos_3d, max_k)
    real_err = compute_loo_prediction_error(vel_vec, k, graph)
    null_errors = compute_own_geometry_baseline(
        vel_vec, k, K_SHUFFLE, n_permutations, seed, noise_frac, graph
    )
    baseline_mean = np.mean(null_errors)
    ratio = real_err / baseline_mean if baseline_mean > 1e-12 else np.nan
    return {
        "real_error": real_err,
        "null_mean": baseline_mean,
        "R": ratio,
        "p": (np.count_nonzero(null_errors <= real_err) + 1) / (len(null_errors) + 1)
    }


def main():
    print("🔬 TRACEBIND V11: Seed Reproducibility Verification")
    print("=" * 80)

    results = []
    for cluster in CLUSTERS:
        input_file = os.path.join(DATA_DIR, f"{cluster}_cg22_dr3_crossmatched.csv")
        if not os.path.exists(input_file):
            continue

        df_original = pd.read_csv(input_file)
        n_stars = len(df_original)
        n_subsample = max(K_SHUFFLE + 5, int(round(n_stars * SUBSAMPLE_FRACTION)))

        # Observed R computed once per cluster (seed-independent reference)
        obs = run_tracebind(df_original, K_PREDICT, NOISE_FRACTION, SEEDS[0], N_PERM_OBSERVED)
        r_obs = obs["R"]

        print(f"\n{cluster.upper()} (N={n_stars}, observed R={r_obs:.4f})")
        print(f"{'Seed':<12} {'Mean R':>10} {'Bias':>10} {'Std':>10} {'CV':>10}")
        print("-" * 56)

        for seed in SEEDS:
            rng_subsample = np.random.default_rng(seed)       # Subsampling RNG
            rng_permutation = np.random.default_rng(seed * 7) # Independent permutation RNG

            ratios = []
            for i in range(N_SUBSAMPLES):
                indices = rng_subsample.choice(n_stars, size=n_subsample, replace=False)
                df_sample = df_original.iloc[indices].reset_index(drop=True)
                perm_seed = int(rng_permutation.integers(0, 1e9))
                res = run_tracebind(df_sample, K_PREDICT, NOISE_FRACTION, perm_seed, N_PERM_SUBSAMPLE)
                if not np.isnan(res["R"]):
                    ratios.append(res["R"])

            mean_r = np.mean(ratios)
            bias = mean_r - r_obs
            std_r = np.std(ratios, ddof=1)
            cv = std_r / mean_r if mean_r > 0 else np.nan

            print(f"{seed:<12} {mean_r:>10.4f} {bias:>+10.4f} {std_r:>10.4f} {cv:>10.4f}")
            results.append({
                "cluster": cluster, "seed": seed,
                "mean_R": mean_r, "bias": bias, "std_R": std_r, "cv": cv
            })

    # Data-driven summary (no hard-coded thresholds)
    summary_df = pd.DataFrame(results)
    agg = summary_df.groupby("cluster").agg(
        mean_of_means=("mean_R", "mean"),
        sd_of_means=("mean_R", "std"),
        range_of_means=("mean_R", lambda x: x.max() - x.min()),
        mean_cv=("cv", "mean")
    )
    print("\n📊 Cross-seed variability summary:")
    print(agg.to_string(float_format="%.4f"))

    out_path = os.path.join(DATA_DIR, "tracebind_v11_seed_verification.csv")
    summary_df.to_csv(out_path, index=False)
    print(f"\n💾 Saved to {out_path}")


if __name__ == "__main__":
    main()