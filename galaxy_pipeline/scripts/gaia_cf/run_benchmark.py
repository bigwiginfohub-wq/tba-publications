"""
TRACEBIND Generic Benchmark Runner
Runs the frozen V11 metric + bootstrap framework on any local cluster CSV.
Usage: python run_benchmark.py <path_to_cluster_csv> <cluster_name>
License: CC0 1.0 Universal
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, mannwhitneyu

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up TWO levels: gaia_cf -> scripts -> GaiaProject
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, _SCRIPT_DIR)

from tracebind.metric import (
    astrometry_to_cartesian,
    compute_ratio_distribution,
    TRACEBIND_METRIC_VERSION,
)
from astroquery.gaia import Gaia

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "real")
K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 200
RANDOM_SEED_BASE = 42
N_BOOTSTRAP_FIELDS = 50
SEPARATION_Q_SIG = 97.5
SEPARATION_Q_CTRL = 2.5
MIN_FIELD_SIZE = 60


def load_cluster(path, name):
    """Load any cluster CSV with standard columns."""
    if not os.path.exists(path):
        raise RuntimeError(f"Cluster file not found: {path}")
    
    df = pd.read_csv(path)
    required = {"source_id", "ra", "dec", "parallax", "pmra", "pmdec", "phot_g_mean_mag"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"{name} missing columns: {missing}")
        
    # Basic quality cuts
    df = df[(df["parallax"] > 0) & (df["phot_g_mean_mag"] < 18.0)].copy()
    df = df.reset_index(drop=True)
    print(f"📂 Loaded {len(df)} members for {name}")
    return df


def get_field_pool(cluster_df, cluster_name):
    """Query Gaia ONCE for a field pool specific to this cluster's sky location."""
    cache_file = os.path.join(OUTPUT_DIR, f"field_pool_{cluster_name}.csv")
    if os.path.exists(cache_file):
        print(f"📂 Using cached field pool for {cluster_name}")
        return pd.read_csv(cache_file)

    ra_min = cluster_df["ra"].min() - 10
    ra_max = cluster_df["ra"].max() + 10
    dec_min = cluster_df["dec"].min() - 10
    dec_max = cluster_df["dec"].max() + 10

    print(f"🔭 Querying Gaia for {cluster_name} field pool...")
    query = f"""
    SELECT TOP 20000 g.source_id, g.ra, g.dec, g.parallax, g.pmra, g.pmdec,
           g.phot_g_mean_mag, g.ruwe
    FROM gaiadr3.gaia_source AS g
    WHERE g.ra BETWEEN {ra_min} AND {ra_max}
      AND g.dec BETWEEN {dec_min} AND {dec_max}
      AND g.phot_g_mean_mag < 18.0
      AND g.parallax > 0.1
      AND g.parallax < 10.0
    """
    job = Gaia.launch_job(query)
    candidates = job.get_results().to_pandas()
    
    # Exclude cluster members by parallax
    plx_lo = cluster_df["parallax"].quantile(0.01)
    plx_hi = cluster_df["parallax"].quantile(0.99)
    candidates = candidates[(candidates["parallax"] < plx_lo) | (candidates["parallax"] > plx_hi)]
    
    candidates.to_csv(cache_file, index=False)
    print(f"   Pool size: {len(candidates)}")
    return candidates


def run_bootstrap(cluster_df, pool, cluster_name):
    """Run 50 bootstrap realizations."""
    results = []
    print(f"\n⚙️  Running {N_BOOTSTRAP_FIELDS} bootstrap realizations for {cluster_name}...")
    
    for i in range(N_BOOTSTRAP_FIELDS):
        seed = RANDOM_SEED_BASE + i * 100
        rng = np.random.default_rng(seed)
        
        # Stratified Matching
        hyd_g = cluster_df["phot_g_mean_mag"].values
        fld_g = pool["phot_g_mean_mag"].values
        bins = np.linspace(hyd_g.min(), hyd_g.max(), 21)
        
        matched_idx = []
        for j in range(len(bins)-1):
            mask_h = (hyd_g >= bins[j]) & (hyd_g < bins[j+1])
            n_need = mask_h.sum()
            if n_need == 0: continue
            mask_f = (fld_g >= bins[j]) & (fld_g < bins[j+1])
            pool_idx = np.where(mask_f)[0]
            if len(pool_idx) < n_need:
                matched_idx.extend(pool_idx)
            else:
                matched_idx.extend(rng.choice(pool_idx, size=n_need, replace=False))
                
        if len(matched_idx) < MIN_FIELD_SIZE: continue
        field_df = pool.iloc[matched_idx[:len(cluster_df)]].reset_index(drop=True)
        
        ks_stat, _ = ks_2samp(hyd_g, field_df["phot_g_mean_mag"].values)
        
        # Run Metric
        master_rng = np.random.default_rng(RANDOM_SEED_BASE + hash(f"{cluster_name}_{i}") % 1000)
        rng_hyd = np.random.default_rng(master_rng.integers(0, 2**31))
        rng_fld = np.random.default_rng(master_rng.integers(0, 2**31))
        
        pos_c = astrometry_to_cartesian(cluster_df["ra"].values, cluster_df["dec"].values, cluster_df["parallax"].values)
        c_dist = compute_ratio_distribution(pos_c, cluster_df["pmra"].values, cluster_df["pmdec"].values, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_hyd)
        
        pos_f = astrometry_to_cartesian(field_df["ra"].values, field_df["dec"].values, field_df["parallax"].values)
        f_dist = compute_ratio_distribution(pos_f, field_df["pmra"].values, field_df["pmdec"].values, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_fld)
        
        if len(c_dist) == 0 or len(f_dist) == 0: continue
        
        sig_q = np.percentile(c_dist, SEPARATION_Q_SIG)
        ctrl_q = np.percentile(f_dist, SEPARATION_Q_CTRL)
        separated = sig_q < ctrl_q
        
        mw_stat, mw_p = mannwhitneyu(c_dist, f_dist, alternative='less')
        effect_size = mw_stat / (len(c_dist) * len(f_dist)) if not np.isnan(mw_stat) else 0
        
        results.append({
            "realization": i,
            "ks_stat": ks_stat,
            "cluster_median": np.median(c_dist),
            "field_median": np.median(f_dist),
            "separated": separated,
            "effect_size": effect_size
        })
        
        if i % 10 == 0: print(f"   ... {i}/{N_BOOTSTRAP_FIELDS}")
        
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=str, help="Path to cluster CSV")
    parser.add_argument("name", type=str, help="Cluster name (e.g., hyades, pleiades)")
    args = parser.parse_args()
    
    print(f"🔬 TRACEBIND BENCHMARK: {args.name.upper()}")
    print("=" * 90)
    
    cluster_df = load_cluster(args.csv_path, args.name)
    pool = get_field_pool(cluster_df, args.name)
    df_res = run_bootstrap(cluster_df, pool, args.name)
    
    if df_res.empty:
        raise RuntimeError("No valid results generated.")
        
    print("\n" + "=" * 90)
    print(f"📊 RESULTS FOR {args.name.upper()}")
    print("-" * 50)
    print(f"  Cluster Median Ratio:     {df_res['cluster_median'].mean():.4f} ± {df_res['cluster_median'].std():.4f}")
    print(f"  Field Median Ratio:       {df_res['field_median'].mean():.4f} ± {df_res['field_median'].std():.4f}")
    print(f"  Separation Frequency:     {df_res['separated'].sum()}/{len(df_res)} ({100*df_res['separated'].mean():.1f}%)")
    print(f"  Mean KS Statistic:        {df_res['ks_stat'].mean():.4f}")
    
    # Save Report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = {
        "cluster": args.name,
        "metric_version": TRACEBIND_METRIC_VERSION,
        "summary": {
            "cluster_median_mean": float(df_res['cluster_median'].mean()),
            "field_median_mean": float(df_res['field_median'].mean()),
            "separation_frequency": float(df_res['separated'].mean()),
            "mean_ks": float(df_res['ks_stat'].mean())
        },
        "details": df_res.to_dict(orient='records')
    }
    
    with open(os.path.join(OUTPUT_DIR, f"benchmark_{args.name}.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\n💾 Report saved to benchmark_{args.name}.json")

if __name__ == "__main__":
    main()