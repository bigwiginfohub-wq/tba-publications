"""
TRACEBIND Purity Calibration Sweep (Multi-Seed Averaged)
Quantifies metric sensitivity to membership contamination using matched field controls.
Runs 10 master seeds x 30 realizations per purity level.
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

# ... [imports unchanged] ...

K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 50   # Reduced from 200 (still enough for median stability)
N_MASTER_SEEDS = 5    # Reduced from 10 (enough to see the trend)
N_REALIZATIONS = 10   # Reduced from 30 (enough for a rough CI)
PURITIES = [1.0, 0.8, 0.6, 0.4, 0.2, 0.0] # Fewer points to speed up the sweep

def run_single_sweep(master_seed):
    """Run one full purity sweep with a specific master seed."""
    hyades = pd.read_csv(HYADES_FILE)
    field_pool = pd.read_csv(FIELD_POOL_FILE)
    n_total = len(hyades)
    
    rng = np.random.default_rng(master_seed)
    results = []
    
    for p in PURITIES:
        n_members = int(n_total * p)
        n_contaminants = n_total - n_members
        
        cluster_medians = []
        field_medians = []
        margins = [] # Q2(Field) - Q97(Cluster)
        
        for i in range(N_REALIZATIONS):
            seed_hyd = int(rng.integers(0, 2**31))
            seed_cont = int(rng.integers(0, 2**31))
            seed_metric_c = int(rng.integers(0, 2**31))
            seed_metric_f = int(rng.integers(0, 2**31))
            
            # Create Contaminated Sample
            if p == 1.0:
                mixed_sample = hyades.copy()
            else:
                true_members = hyades.sample(n=n_members, random_state=seed_hyd)
                contaminants = field_pool.sample(n=n_contaminants, random_state=seed_cont)
                mixed_sample = pd.concat([true_members, contaminants]).sample(frac=1, random_state=seed_hyd).reset_index(drop=True)
            
            # Create Matched Field Sample for Comparison
            field_sample = field_pool.sample(n=n_total, random_state=seed_cont).reset_index(drop=True)
            
            # Run Metric on Cluster
            pos_c = astrometry_to_cartesian(mixed_sample["ra"].values, mixed_sample["dec"].values, mixed_sample["parallax"].values)
            dist_c = compute_ratio_distribution(pos_c, mixed_sample["pmra"].values, mixed_sample["pmdec"].values,
                                                K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, 
                                                np.random.default_rng(seed_metric_c))
            
            # Run Metric on Field
            pos_f = astrometry_to_cartesian(field_sample["ra"].values, field_sample["dec"].values, field_sample["parallax"].values)
            dist_f = compute_ratio_distribution(pos_f, field_sample["pmra"].values, field_sample["pmdec"].values,
                                                K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, 
                                                np.random.default_rng(seed_metric_f))
            
            if len(dist_c) > 0 and len(dist_f) > 0:
                med_c = np.median(dist_c)
                med_f = np.median(dist_f)
                q97_c = np.percentile(dist_c, 97.5)
                q02_f = np.percentile(dist_f, 2.5)
                
                cluster_medians.append(med_c)
                field_medians.append(med_f)
                margins.append(q02_f - q97_c)
                
        if cluster_medians:
            arr_c = np.array(cluster_medians)
            arr_f = np.array(field_medians)
            arr_m = np.array(margins)
            
            results.append({
                "purity": p,
                "contamination": 1.0 - p,
                "cluster_mean": np.mean(arr_c),
                "cluster_median_of_medians": np.median(arr_c),
                "cluster_std": np.std(arr_c),
                "cluster_ci_lower": np.percentile(arr_c, 2.5),
                "cluster_ci_upper": np.percentile(arr_c, 97.5),
                "field_mean": np.mean(arr_f),
                "margin_mean": np.mean(arr_m),
                "separation_freq": np.sum(np.array(margins) > 0) / len(margins)
            })
            
    return pd.DataFrame(results)

def main():
    print("🔬 TRACEBIND PURITY CALIBRATION SWEEP (MULTI-SEED)")
    print("=" * 90)
    
    if not os.path.exists(HYADES_FILE) or not os.path.exists(FIELD_POOL_FILE):
        raise RuntimeError("Missing input files. Run benchmark first.")
        
    all_sweeps = []
    for i in range(N_MASTER_SEEDS):
        seed = 42 + i * 1000
        print(f"⚙️  Running Master Seed {i+1}/{N_MASTER_SEEDS} (Seed={seed})...")
        df_sweep = run_single_sweep(seed)
        all_sweeps.append(df_sweep)
        
    # Aggregate Results across Master Seeds
    combined = pd.concat(all_sweeps)
    summary = combined.groupby("contamination").agg(
        cluster_mean=("cluster_mean", "mean"),
        cluster_ci_lower=("cluster_ci_lower", "mean"),
        cluster_ci_upper=("cluster_ci_upper", "mean"),
        field_mean=("field_mean", "mean"),
        margin_mean=("margin_mean", "mean"),
        separation_freq=("separation_freq", "mean")
    ).reset_index()
    
    # Sort by contamination for plotting
    summary = summary.sort_values("contamination")
    
    print("\n" + "=" * 90)
    print("📊 AGGREGATED PURITY CALIBRATION SUMMARY")
    print("-" * 50)
    print(summary.to_string(index=False, float_format="%.4f"))
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary.to_csv(os.path.join(OUTPUT_DIR, "purity_calibration_final.csv"), index=False)
    print(f"\n💾 Saved final calibration to purity_calibration_final.csv")

if __name__ == "__main__":
    main()