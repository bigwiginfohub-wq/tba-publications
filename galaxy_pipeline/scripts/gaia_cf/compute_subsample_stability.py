"""Compute subsampling stability intervals for TRACEBIND-V11 coherence ratio R."""
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
SUBSAMPLE_FRACTIONS = [0.60, 0.70, 0.80, 0.90]
RANDOM_SEED = 42
K_PREDICT = 30
K_SHUFFLE = 50
N_PERM_OBSERVED = 1000   # Full permutations for observed statistic
N_PERM_SUBSAMPLE = 500   # Production value; reduced to 100 during development
NOISE_FRACTION = 0.10

# === PATHS ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")

CLUSTERS = ["pleiades", "hyades"]


def run_tracebind(df, k, noise_frac, seed, n_permutations):
    """Run full V11 pipeline with configurable permutation count."""
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
    p_value = (np.count_nonzero(null_errors <= real_err) + 1) / (len(null_errors) + 1)
    ratio = real_err / baseline_mean if baseline_mean > 1e-12 else np.nan

    return {
        "real_error": real_err,
        "null_mean": baseline_mean,
        "R": ratio,
        "p": p_value
    }


def main():
    print("🔬 TRACEBIND V11: Subsampling Stability Analysis")
    print("=" * 80)
    print(f"   N_SUBSAMPLES={N_SUBSAMPLES}")
    print(f"   FRACTIONS TESTED: {SUBSAMPLE_FRACTIONS}")
    print(f"   Permutations: observed={N_PERM_OBSERVED}, subsample={N_PERM_SUBSAMPLE}\n")

    rng = np.random.default_rng(RANDOM_SEED)
    all_replicates = []
    summary_rows = []

    for cluster in CLUSTERS:
        input_file = os.path.join(DATA_DIR, f"{cluster}_cg22_dr3_crossmatched.csv")
        if not os.path.exists(input_file):
            print(f"️ Skipping {cluster}: file not found at {input_file}")
            continue

        df_original = pd.read_csv(input_file)
        n_stars = len(df_original)

        # Compute observed R on FULL sample with full permutations
        obs_results = run_tracebind(
            df_original, K_PREDICT, NOISE_FRACTION, RANDOM_SEED, N_PERM_OBSERVED
        )
        r_observed = obs_results["R"]

        print(f"📊 {cluster.upper()} (N={n_stars}): Observed R = {r_observed:.4f}")
        print(f"   Real error: {obs_results['real_error']:.4f} km/s")
        print(f"   Null mean : {obs_results['null_mean']:.4f} km/s\n")

        cluster_summary = {
            "cluster": cluster,
            "n_stars_full": n_stars,
            "r_observed": r_observed,
            "obs_real_error": obs_results["real_error"],
            "obs_null_mean": obs_results["null_mean"],
            "obs_p": obs_results["p"]
        }

        for frac in SUBSAMPLE_FRACTIONS:
            n_subsample = max(K_SHUFFLE + 5, int(round(n_stars * frac)))
            print(f"   Testing fraction={frac:.0%} (n={n_subsample})...")

            subsample_ratios = []
            for i in range(N_SUBSAMPLES):
                indices = rng.choice(n_stars, size=n_subsample, replace=False)
                df_sample = df_original.iloc[indices].reset_index(drop=True)

                sample_results = run_tracebind(
                    df_sample, K_PREDICT, NOISE_FRACTION,
                    RANDOM_SEED + i, N_PERM_SUBSAMPLE
                )
                r_sub = sample_results["R"]

                if not np.isnan(r_sub):
                    subsample_ratios.append(r_sub)
                    all_replicates.append({
                        "cluster": cluster,
                        "fraction": frac,
                        "subsample_id": i + 1,
                        "n_stars": n_subsample,
                        "R": r_sub,
                        "real_error": sample_results["real_error"],
                        "null_mean": sample_results["null_mean"]
                    })

            if len(subsample_ratios) == 0:
                print(f"      ⚠️ No valid subsamples.")
                continue

            subsample_ratios = np.array(subsample_ratios)
            q025 = np.percentile(subsample_ratios, 2.5)
            q975 = np.percentile(subsample_ratios, 97.5)
            bias = np.mean(subsample_ratios) - r_observed

            cluster_summary[f"frac_{int(frac*100)}_mean"] = np.mean(subsample_ratios)
            cluster_summary[f"frac_{int(frac*100)}_median"] = np.median(subsample_ratios)
            cluster_summary[f"frac_{int(frac*100)}_std"] = np.std(subsample_ratios, ddof=1)
            cluster_summary[f"frac_{int(frac*100)}_bias"] = bias
            cluster_summary[f"frac_{int(frac*100)}_q025"] = q025
            cluster_summary[f"frac_{int(frac*100)}_q975"] = q975
            cluster_summary[f"frac_{int(frac*100)}_frac_R_lt_1"] = np.mean(subsample_ratios < 1.0)

            print(f"      Mean={np.mean(subsample_ratios):.4f}, Bias={bias:+.4f}, "
                  f"Stability [{q025:.4f}, {q975:.4f}], "
                  f"Frac(R<1)={np.mean(subsample_ratios < 1.0):.3f}")

        summary_rows.append(cluster_summary)
        print()

    # Save individual replicates
    replicates_df = pd.DataFrame(all_replicates)
    rep_path = os.path.join(DATA_DIR, "tracebind_v11_subsample_replicates.csv")
    replicates_df.to_csv(rep_path, index=False)
    print(f"💾 Individual replicates saved to {rep_path}")

    # Save summary with observed statistics and bias
    summary_df = pd.DataFrame(summary_rows)
    summary_path = os.path.join(DATA_DIR, "tracebind_v11_subsample_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"💾 Summary saved to {summary_path}")

    # Empirical dominance probability at primary fraction (80%)
    primary_frac = 0.80
    ple_r = replicates_df[
        (replicates_df["cluster"] == "pleiades") & 
        (replicates_df["fraction"] == primary_frac)
    ]["R"].values
    hya_r = replicates_df[
        (replicates_df["cluster"] == "hyades") & 
        (replicates_df["fraction"] == primary_frac)
    ]["R"].values

    if len(ple_r) > 0 and len(hya_r) > 0:
        emp_dominance = np.mean(hya_r[:, None] < ple_r[None, :])
        print(f"\n Empirical dominance probability ({primary_frac:.0%} subsamples):")
        print(f"   Hyades exhibited lower R than Pleiades in {emp_dominance:.1%} of pairwise comparisons")
        print(f"   Based on {len(hya_r)} × {len(ple_r)} non-independent comparisons")


if __name__ == "__main__":
    main()