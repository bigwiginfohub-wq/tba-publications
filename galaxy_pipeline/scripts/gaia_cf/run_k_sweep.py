"""
TRACEBIND K-SENSITIVITY SWEEP (BOOTSTRAPPED)
Tests robustness of Hyades coherence signal to neighborhood size K_PREDICT.
Holds K_SHUFFLE=50, field pool, and cluster sample FIXED across all k values.
Reports mean ± SD for cluster, field, delta, and separation frequency.
License: CC0 1.0 Universal
"""
import os
import sys
import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up TWO levels: gaia_cf -> scripts -> GaiaProject
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, _SCRIPT_DIR)

from tracebind.metric import (
    astrometry_to_cartesian,
    compute_ratio_distribution,
    TRACEBIND_METRIC_VERSION,
)

REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "real")
HYADES_FILE = os.path.join(REF_DIR, "hyades_dr3_high_quality.csv")
FIELD_POOL_FILE = os.path.join(OUTPUT_DIR, "field_candidates_pool_hyades.csv")

K_PREDICT_VALUES = [20, 25, 30, 35, 40]
K_SHUFFLE_FIXED = 50          # Held constant to isolate K_PREDICT effect
N_PERMUTATIONS = 200
N_BOOTSTRAP = 20              # Reuse bootstrap framework from Phase 4
RANDOM_SEED_BASE = 42
SEPARATION_Q_SIG = 97.5
SEPARATION_Q_CTRL = 2.5


def main():
    print("🔬 TRACEBIND K-SENSITIVITY SWEEP (BOOTSTRAPPED)")
    print("=" * 90)

    hyades = pd.read_csv(HYADES_FILE)
    field_pool = pd.read_csv(FIELD_POOL_FILE)
    n_total = len(hyades)

    # FIX samples once — reuse identically for every k value
    rng_fixed = np.random.default_rng(RANDOM_SEED_BASE)
    cluster_sample = hyades.sample(n=n_total, random_state=int(rng_fixed.integers(0, 2**31))).reset_index(drop=True)
    field_sample = field_pool.sample(n=n_total, random_state=int(rng_fixed.integers(0, 2**31))).reset_index(drop=True)

    results = []

    for k in K_PREDICT_VALUES:
        print(f"\n⚙️  Testing K_PREDICT={k} (K_SHUFFLE={K_SHUFFLE_FIXED} fixed)...")

        cluster_medians = []
        field_medians = []
        deltas = []
        separations = []

        for b in range(N_BOOTSTRAP):
            seed_c = int(rng_fixed.integers(0, 2**31))
            seed_f = int(rng_fixed.integers(0, 2**31))

            pos_c = astrometry_to_cartesian(
                cluster_sample["ra"].values,
                cluster_sample["dec"].values,
                cluster_sample["parallax"].values,
            )
            dist_c = compute_ratio_distribution(
                pos_c,
                cluster_sample["pmra"].values,
                cluster_sample["pmdec"].values,
                k, K_SHUFFLE_FIXED, N_PERMUTATIONS,
                np.random.default_rng(seed_c),
            )

            pos_f = astrometry_to_cartesian(
                field_sample["ra"].values,
                field_sample["dec"].values,
                field_sample["parallax"].values,
            )
            dist_f = compute_ratio_distribution(
                pos_f,
                field_sample["pmra"].values,
                field_sample["pmdec"].values,
                k, K_SHUFFLE_FIXED, N_PERMUTATIONS,
                np.random.default_rng(seed_f),
            )

            if len(dist_c) == 0 or len(dist_f) == 0:
                continue

            med_c = np.median(dist_c)
            med_f = np.median(dist_f)
            q97_c = np.percentile(dist_c, SEPARATION_Q_SIG)
            q02_f = np.percentile(dist_f, SEPARATION_Q_CTRL)

            cluster_medians.append(med_c)
            field_medians.append(med_f)
            deltas.append(med_f - med_c)
            separations.append(q02_f > q97_c)

        arr_c = np.array(cluster_medians)
        arr_f = np.array(field_medians)
        arr_d = np.array(deltas)
        sep_freq = np.mean(separations) if separations else 0.0

        results.append({
            "k_predict": k,
            "k_shuffle": K_SHUFFLE_FIXED,
            "cluster_mean": np.mean(arr_c),
            "cluster_std": np.std(arr_c),
            "field_mean": np.mean(arr_f),
            "field_std": np.std(arr_f),
            "delta_mean": np.mean(arr_d),
            "delta_std": np.std(arr_d),
            "separation_freq": sep_freq,
            "n_realizations": len(arr_c),
        })

        print(f"   Cluster: {np.mean(arr_c):.4f} ± {np.std(arr_c):.4f} | "
              f"Field: {np.mean(arr_f):.4f} ± {np.std(arr_f):.4f} | "
              f"Δ: {np.mean(arr_d):.4f} ± {np.std(arr_d):.4f} | "
              f"Sep.Freq: {sep_freq:.0%}")

    df_res = pd.DataFrame(results)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUTPUT_DIR, "k_sensitivity_hyades_bootstrapped.csv")
    df_res.to_csv(csv_path, index=False)

    print("\n" + "=" * 90)
    print("📊 K-SENSITIVITY SUMMARY (BOOTSTRAPPED)")
    print("-" * 50)
    print(df_res.to_string(index=False, float_format="%.4f"))
    print(f"\n💾 Saved to {csv_path}")

    # Report coefficient of variation for cluster median
    cv = df_res["cluster_std"].mean() / df_res["cluster_mean"].mean()
    print(f"\nCluster Median CV: {cv:.4f} ({cv*100:.1f}%)")
    print(f"Delta Mean Range: [{df_res['delta_mean'].min():.4f}, {df_res['delta_mean'].max():.4f}]")


if __name__ == "__main__":
    main()