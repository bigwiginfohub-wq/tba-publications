import pandas as pd
import numpy as np
import os
from scipy.stats import pearsonr, circstd

def test_angular_dispersion():
    input_file = 'data/gaia_phase1_scaled_10k.csv'
    if not os.path.exists(input_file):
        input_file = 'gaia_phase1_scaled_10k.csv'
        
    df = pd.read_csv(input_file)
    df = df.dropna(subset=['ra', 'dec', 'pmra', 'pmdec'])
    df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    df = df[df['pm_mag'] > 0.1]
    
    print(f"📋 Loaded {len(df)} sources for Angular Dispersion Test.\n")

    # 2D Sky Binning
    ra_bins = np.linspace(0, 360, 13)
    dec_bins = np.linspace(-90, 90, 7)
    df['ra_bin'] = np.digitize(df['ra'], ra_bins)
    df['dec_bin'] = np.digitize(df['dec'], dec_bins)

    results = []
    for (rb, db), group in df.groupby(['ra_bin', 'dec_bin']):
        if len(group) < 20: continue
        
        # 1. Calculate Angles (Theta)
        angles = np.arctan2(group['pmdec'].values, group['pmra'].values)
        
        # 2. Circular Standard Deviation (The spread of directions)
        # circstd handles the wrap-around at +/- pi correctly
        ang_disp = circstd(angles) 
        
        # 3. Directional Coherence (Cf)
        ux = group['pmra'].values / group['pm_mag'].values
        uy = group['pmdec'].values / group['pm_mag'].values
        cf = np.sqrt(np.mean(ux)**2 + np.mean(uy)**2)
        
        results.append({
            'ra_bin': rb, 'dec_bin': db,
            'stars': len(group),
            'cf': cf,
            'ang_disp_rad': ang_disp
        })

    res_df = pd.DataFrame(results)
    
    # Correlation
    r, p = pearsonr(res_df['cf'], res_df['ang_disp_rad'])
    
    print("="*80)
    print("FINAL SANITY CHECK: COHERENCE (Cf) vs. ANGULAR DISPERSION")
    print("="*80)
    print("Mathematical Expectation: Since Cf is the Mean Resultant Length (R),")
    print("it MUST strongly and inversely correlate with Circular Standard Deviation.")
    print("If r ≈ -1.0, the metric is mathematically sound as a directional statistic.\n")
    
    print(f"Pearson Correlation (Cf vs Angular Dispersion): r = {r:.4f} (p = {p:.4e})\n")
    
    if r < -0.95:
        print("✅ MATHEMATICAL VALIDATION SUCCESSFUL!")
        print("   Cf behaves exactly as a robust directional statistic.")
        print("   It perfectly quantifies the inverse of angular dispersion.")
    else:
        print("⚠️ UNEXPECTED RESULT")
        print("   The metric does not perfectly align with standard circular statistics.")
        
    print("\n--- SAMPLE VOXELS ---")
    print(f"{'Patch':<10} | {'Stars':<6} | {'Cf (Alignment)':<14} | {'Ang Disp (rad)':<14}")
    print("-" * 55)
    for _, row in res_df.sort_values('cf', ascending=False).head(10).iterrows():
        print(f"{row['ra_bin']}-{row['dec_bin']:<7} | {int(row['stars']):<6} | {row['cf']:<14.4f} | {row['ang_disp_rad']:<14.4f}")
        
    print("="*80)

if __name__ == "__main__":
    test_angular_dispersion()