import pandas as pd
import numpy as np
import os
from scipy.stats import pearsonr

def test_3d_physical_coherence():
    input_file = 'data/gaia_phase1_scaled_10k.csv'
    if not os.path.exists(input_file):
        input_file = 'gaia_phase1_scaled_10k.csv'
        
    df = pd.read_csv(input_file)
    
    # Strict astrometric cuts for reliable 3D mapping
    df = df.dropna(subset=['ra', 'dec', 'pmra', 'pmdec', 'parallax', 'parallax_error'])
    df = df[df['parallax'] > 0]
    df = df[(df['parallax_error'] / df['parallax']) < 0.2] # Max 20% distance uncertainty
    
    df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    df = df[df['pm_mag'] > 0.1]
    
    # UPGRADE 1: True Distance Calculation (parsecs)
    df['dist_pc'] = 1000.0 / df['parallax']
    
    print(f"📋 Loaded {len(df)} sources with high-quality 3D astrometry.\n")

    # UPGRADE 2: 3D Voxel Binning (RA, Dec, Distance Shells)
    ra_bins = np.linspace(0, 360, 13)   # 30 deg slices
    dec_bins = np.linspace(-90, 90, 7)  # 30 deg slices
    # Physical distance bins (in parsecs) to separate foreground from background
    dist_bins = [0, 150, 300, 600, 1200, 2500, 5000, 100000] 
    
    df['ra_bin'] = np.digitize(df['ra'], ra_bins)
    df['dec_bin'] = np.digitize(df['dec'], dec_bins)
    df['dist_bin'] = pd.cut(df['dist_pc'], bins=dist_bins, labels=False)

    results = []
    for (rb, db, dib), group in df.groupby(['ra_bin', 'dec_bin', 'dist_bin']):
        if len(group) < 15: continue # Require statistical significance in a 3D voxel
        
        # Directional Coherence (Cf)
        ux = group['pmra'].values / group['pm_mag'].values
        uy = group['pmdec'].values / group['pm_mag'].values
        cf = np.sqrt(np.mean(ux)**2 + np.mean(uy)**2)
        
        # Physical Dispersions
        sigma_pm = group['pm_mag'].std()
        mean_dist = group['dist_pc'].mean()
        sigma_dist = group['dist_pc'].std()
        
        # UPGRADE 1b: Coefficient of Variation (CV) for distance
        # Measures relative depth spread, independent of absolute distance
        cv_dist = sigma_dist / mean_dist if mean_dist > 0 else np.nan
        
        results.append({
            'ra_bin': rb, 'dec_bin': db, 'dist_bin': dib,
            'stars': len(group),
            'cf': cf,
            'sigma_pm': sigma_pm,
            'mean_dist_pc': mean_dist,
            'cv_dist': cv_dist
        })

    res_df = pd.DataFrame(results)
    res_df = res_df.dropna(subset=['cv_dist'])
    
    # Correlations
    r_dist, p_dist = pearsonr(res_df['cf'], res_df['cv_dist'])
    r_pm, p_pm = pearsonr(res_df['cf'], res_df['sigma_pm'])
    
    print("="*80)
    print("MORPHEUS 3D PHYSICAL SANITY CHECK: COHERENCE vs. 3D DISPERSION")
    print("="*80)
    print("Question: Do highly coherent 3D voxels also share the same speed and depth?")
    print("If yes (negative correlation), Cf traces real physical structures.")
    print("If no (zero correlation), Cf is just directional alignment.\n")
    
    print(f"1. Coherence (Cf) vs Distance CV       : r = {r_dist:.3f} (p={p_dist:.4f})")
    print(f"2. Coherence (Cf) vs Speed Dispersion  : r = {r_pm:.3f} (p={p_pm:.4f})\n")
    
    # UPGRADE 3: Rank-based Structure Score
    # High Cf gets a high rank. Low CV (tight depth) gets a high rank.
    res_df['cf_rank'] = res_df['cf'].rank(pct=True)
    res_df['cv_rank'] = res_df['cv_dist'].rank(pct=True, ascending=False) 
    res_df['structure_score'] = res_df['cf_rank'] + res_df['cv_rank']
    
    top_structures = res_df.sort_values('structure_score', ascending=False).head(10)
    
    print("🌌 TOP 10 'TRUE PHYSICAL STRUCTURES' (Ranked by Score = Cf + Inverse CV)")
    print(f"{'Voxel':<12} | {'Stars':<6} | {'Cf':<6} | {'Dist (pc)':<10} | {'CV_dist':<8} | {'σ_pm':<6}")
    print("-" * 70)
    for _, row in top_structures.iterrows():
        print(f"{row['ra_bin']}-{row['dec_bin']}-{row['dist_bin']:<4} | {int(row['stars']):<6} | {row['cf']:<6.3f} | {row['mean_dist_pc']:<10.0f} | {row['cv_dist']:<8.3f} | {row['sigma_pm']:<6.2f}")
        
    print("\n" + "="*80)
    if r_dist < -0.3 and p_dist < 0.05:
        print("✅ VALIDATION SUCCESSFUL!")
        print("   High directional coherence strongly correlates with low depth dispersion.")
        print("   Cf is successfully tracing compact, physical 3D stellar structures.")
    else:
        print("⚠️ INCONCLUSIVE / WEAK CORRELATION")
        print("   Directional coherence does not strictly guarantee physical compactness.")
        print("   Cf measures kinematic alignment, which may include line-of-sight projections.")
    print("="*80)

if __name__ == "__main__":
    test_3d_physical_coherence()