import pandas as pd
import numpy as np
import os

def run_final_permutation_test():
    input_file = 'data/gaia_phase1_scaled_10k.csv'
    if not os.path.exists(input_file):
        input_file = 'gaia_phase1_scaled_10k.csv'
        
    df = pd.read_csv(input_file)
    df = df.dropna(subset=['ra', 'dec', 'pmra', 'pmdec'])
    df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    df = df[df['pm_mag'] > 0.1]
    df = df.reset_index(drop=True)

    print(f"📋 Loaded {len(df)} sources for Final Permutation Test.\n")

    # MORPHEUS OPTIMIZATION: Pre-calculate unit vectors ONCE
    ux_vals = df['pmra'].values / df['pm_mag'].values
    uy_vals = df['pmdec'].values / df['pm_mag'].values

    # Binning logic
    ra_bins = np.linspace(0, 360, 13)
    dec_bins = np.linspace(-90, 90, 7)
    df['ra_bin'] = np.digitize(df['ra'], ra_bins)
    df['dec_bin'] = np.digitize(df['dec'], dec_bins)
    
    # Pre-calculate group indices for maximum speed
    valid_groups = {}
    for (rb, db), group_idx in df.groupby(['ra_bin', 'dec_bin']).groups.items():
        if len(group_idx) >= 20:
            valid_groups[(rb, db)] = group_idx.values

    def calculate_metrics(ux_arr, uy_arr):
        cfs = []
        for group_idx in valid_groups.values():
            mean_ux = np.mean(ux_arr[group_idx])
            mean_uy = np.mean(uy_arr[group_idx])
            cf = np.sqrt(mean_ux**2 + mean_uy**2)
            cfs.append(cf)
            
        cfs = np.array(cfs)
        if len(cfs) == 0:
            return {'max': 0, 'mean': 0, 'p95': 0, 'top5_mean': 0}
            
        sorted_cfs = np.sort(cfs)
        return {
            'max': sorted_cfs[-1],
            'mean': np.mean(sorted_cfs),
            'p95': np.percentile(sorted_cfs, 95),
            'top5_mean': np.mean(sorted_cfs[-5:]) if len(sorted_cfs) >= 5 else np.mean(sorted_cfs)
        }

    # 1. OBSERVED STATISTICS
    obs_metrics = calculate_metrics(ux_vals, uy_vals)
    
    print("="*85)
    print("PART 1: OBSERVED SKY METRICS")
    print("="*85)
    for k, v in obs_metrics.items():
        print(f"  {k:<12}: {v:.4f}")

    # 2. PERMUTATION TEST (The Null Model)
    print("\n" + "="*85)
    print("PART 2: PERMUTATION TEST (1,000 Shuffled Skies)")
    print("="*85)
    print("Shuffling unit vectors to destroy spatial correlations...")
    
    np.random.seed(42)
    N_ITERATIONS = 1000
    
    null_distributions = {'max': [], 'mean': [], 'p95': [], 'top5_mean': []}
    
    for i in range(N_ITERATIONS):
        # Shuffle the unit vectors globally
        shuffle_idx = np.random.permutation(len(df))
        shuf_ux = ux_vals[shuffle_idx]
        shuf_uy = uy_vals[shuffle_idx]
        
        shuf_metrics = calculate_metrics(shuf_ux, shuf_uy)
        
        for k in null_distributions.keys():
            null_distributions[k].append(shuf_metrics[k])
            
        if (i + 1) % 250 == 0:
            print(f"  Completed {i+1}/{N_ITERATIONS} permutations...")

    for k in null_distributions.keys():
        null_distributions[k] = np.array(null_distributions[k])

    # 3. CALCULATE P-VALUES & Z-SCORES
    print("\n" + "="*85)
    print("PART 3: STATISTICAL SIGNIFICANCE & EFFECT SIZES")
    print("="*85)
    print(f"{'Metric':<12} | {'Observed':>8} | {'Null Mean':>9} | {'Null Max':>8} | {'p-value':>8} | {'Z-Score':>8}")
    print("-" * 75)
    
    for k in ['max', 'mean', 'p95', 'top5_mean']:
        obs_val = obs_metrics[k]
        null_arr = null_distributions[k]
        
        p_val = np.sum(null_arr >= obs_val) / N_ITERATIONS
        z_score = (obs_val - np.mean(null_arr)) / np.std(null_arr) if np.std(null_arr) > 0 else 0
        
        print(f"{k:<12} | {obs_val:>8.4f} | {np.mean(null_arr):>9.4f} | {np.max(null_arr):>8.4f} | {p_val:>8.4f} | {z_score:>+8.2f}")

    # 4. SAVE NULL DISTRIBUTION FOR PAPER PLOTTING
    os.makedirs('data', exist_ok=True)
    out_csv = 'data/phase_c_null_distribution_final.csv'
    pd.DataFrame(null_distributions).to_csv(out_csv, index=False)
    print(f"\n💾 Saved full null distributions to {out_csv}")
    
    print("\n" + "="*85)
    print("FINAL VERDICT (MORPHEUS CRITERIA)")
    print("="*85)
    p_mean = np.sum(null_distributions['mean'] >= obs_metrics['mean']) / N_ITERATIONS
    p_p95 = np.sum(null_distributions['p95'] >= obs_metrics['p95']) / N_ITERATIONS
    p_top5 = np.sum(null_distributions['top5_mean'] >= obs_metrics['top5_mean']) / N_ITERATIONS
    
    if p_mean < 0.01 and p_p95 < 0.01 and p_top5 < 0.01:
        print("✅ PUBLISHABLE EMPIRICAL STATEMENT ACHIEVED (p < 0.01)")
        print("   Gaia proper-motion fields exhibit spatial coherence significantly")
        print("   above randomized expectations. The Milky Way's kinematic skeleton")
        print("   is statistically unusual and highly organized.")
    elif p_mean < 0.05 or p_p95 < 0.05:
        print("⚠️ MODERATELY SIGNIFICANT")
        print("   Some global metrics show unusual alignment, but the signal is mixed.")
    else:
        print("❌ NOT SIGNIFICANT (p >= 0.05)")
        print("   The observed coherence naturally emerges from the global PM distribution.")
    print("="*85)

if __name__ == "__main__":
    run_final_permutation_test()