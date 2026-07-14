"""
TRACEBIND V11: Robustness Audit Script
Tests sensitivity to k, noise fraction, and random seed using the single source of truth.
"""
import pandas as pd
import numpy as np
import os
import itertools
from tracebind_v11_core import (
    astrometry_to_tangential_velocity,
    build_neighbor_graph,
    compute_loo_prediction_error,
    compute_own_geometry_baseline
)

# ===== AUDIT CONFIGURATION =====
K_VALUES = [20, 30, 40, 50]
NOISE_FRACTIONS = [0.05, 0.10, 0.20]
SEEDS = [42, 100, 2024]
N_PERMUTATIONS = 500

# === PATHS ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
PLEIADES_FILE = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_cg22_dr3_crossmatched.csv")
HYADES_FILE = os.path.join(_PROJECT_ROOT, "data", "reference", "hyades_cg22_dr3_crossmatched.csv")

def run_audit_for_cluster(df, k, noise_frac, seed, graph):
    """Run V11 on a dataset with specific parameters using a precomputed graph."""
    df = df.dropna(subset=["ra", "dec", "parallax", "pmra", "pmdec"]).copy()
    df = df[df["parallax"] > 0].copy()
    if len(df) <= k: return np.nan, np.nan, np.nan

    _, vel_vec = astrometry_to_tangential_velocity(
        df["ra"].values, df["dec"].values, df["parallax"].values,
        df["pmra"].values, df["pmdec"].values
    )

    # Real Error (slices graph to k internally)
    real_err = compute_loo_prediction_error(vel_vec, k, graph)
    
    # Null Distribution (slices graph to k_shuffle internally)
    null_errors = compute_own_geometry_baseline(
        vel_vec, k, 50, N_PERMUTATIONS, seed, noise_frac, graph
    )
    
    baseline_mean = np.mean(null_errors)
    ratio = real_err / baseline_mean if baseline_mean > 1e-12 else np.nan
    
    return real_err, baseline_mean, ratio

def main():
    print("🔬 TRACEBIND V11 ROBUSTNESS AUDIT")
    print("=" * 80)
    
    pleiades_df = pd.read_csv(PLEIADES_FILE)
    hyades_df = pd.read_csv(HYADES_FILE)
    
    results = []
    total_combos = len(K_VALUES) * len(NOISE_FRACTIONS) * len(SEEDS)
    current = 0
    
    # Precompute graphs once per cluster at max_k
    max_k = max(K_VALUES)
    
    p_pos, _ = astrometry_to_tangential_velocity(
        pleiades_df["ra"].values, pleiades_df["dec"].values, 
        pleiades_df["parallax"].values, pleiades_df["pmra"].values, pleiades_df["pmdec"].values
    )
    plei_graph = build_neighbor_graph(p_pos, max_k)

    h_pos, _ = astrometry_to_tangential_velocity(
        hyades_df["ra"].values, hyades_df["dec"].values, 
        hyades_df["parallax"].values, hyades_df["pmra"].values, hyades_df["pmdec"].values
    )
    hya_graph = build_neighbor_graph(h_pos, max_k)
    
    print(f"Running {total_combos} parameter combinations...")
    
    for k, noise, seed in itertools.product(K_VALUES, NOISE_FRACTIONS, SEEDS):
        current += 1
        _, _, r_ple = run_audit_for_cluster(pleiades_df, k, noise, seed, plei_graph)
        _, _, r_hya = run_audit_for_cluster(hyades_df, k, noise, seed, hya_graph)
        
        if not np.isnan(r_ple) and not np.isnan(r_hya):
            results.append({
                "k": k, 
                "noise_frac": noise, 
                "seed": seed,
                "R_pleiades": r_ple, 
                "R_hyades": r_hya,
                "R_difference": r_ple - r_hya
            })
            
        if current % 10 == 0:
            print(f"   Progress: {current}/{total_combos}")

    audit_df = pd.DataFrame(results)
    output_path = os.path.join(_PROJECT_ROOT, "data", "reference", "tracebind_v11_audit_results.csv")
    audit_df.to_csv(output_path, index=False)
    
    preserved_count = (audit_df["R_hyades"] < audit_df["R_pleiades"]).sum()
    total_valid = len(audit_df)
    
    print("\n✅ Audit Complete.")
    print(f"Ordering (Hyades R < Pleiades R) preserved in {preserved_count}/{total_valid} combinations.")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()