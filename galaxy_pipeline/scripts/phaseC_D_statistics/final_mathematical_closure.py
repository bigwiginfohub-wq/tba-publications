import pandas as pd
import numpy as np
import os
from scipy.stats import circstd

def mathematical_closure_and_phase_c():
    input_file = 'data/gaia_phase1_scaled_10k.csv'
    if not os.path.exists(input_file):
        input_file = 'gaia_phase1_scaled_10k.csv'
        
    df = pd.read_csv(input_file)
    df = df.dropna(subset=['ra', 'dec', 'pmra', 'pmdec'])
    df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    df = df[df['pm_mag'] > 0.1]
    
    print(f"📋 Loaded {len(df)} sources for Final Mathematical Closure.\n")

    # 2D Sky Binning
    ra_bins = np.linspace(0, 360, 13)
    dec_bins = np.linspace(-90, 90, 7)
    df['ra_bin'] = np.digitize(df['ra'], ra_bins)
    df['dec_bin'] = np.digitize(df['dec'], dec_bins)

    results = []
    for (rb, db), group in df.groupby(['ra_bin', 'dec_bin']):
        if len(group) < 20: continue
        
        mean_ra = group['ra'].mean()
        mean_dec = group['dec'].mean()
        
        angles = np.arctan2(group['pmdec'].values, group['pmra'].values)
        ang_disp = circstd(angles) 
        
        ux = group['pmra'].values / group['pm_mag'].values
        uy = group['pmdec'].values / group['pm_mag'].values
        cf = np.sqrt(np.mean(ux)**2 + np.mean(uy)**2)
        
        results.append({
            'ra_bin': rb, 'dec_bin': db,
            'center_ra': mean_ra, 'center_dec': mean_dec,
            'star_count': len(group),
            'cf': cf,
            'ang_disp_rad': ang_disp
        })

    res_df = pd.DataFrame(results)
    
    # =========================================================================
    # PART 1: THEORETICAL RMSE (Mathematical Closure)
    # =========================================================================
    valid_cf = res_df['cf'] > 0
    res_df.loc[valid_cf, 'sigma_pred'] = np.sqrt(-2 * np.log(res_df.loc[valid_cf, 'cf']))
    residuals = res_df.loc[valid_cf, 'ang_disp_rad'] - res_df.loc[valid_cf, 'sigma_pred']
    rmse = np.sqrt(np.mean(residuals**2))
    
    print("="*80)
    print("PART 1: MATHEMATICAL CLOSURE (DIRECTIONAL STATISTICS THEORY)")
    print("="*80)
    print(f"Theoretical Prediction: σ_circ = √(-2 * ln(Cf))")
    print(f"Root Mean Square Error (RMSE): {rmse:.6f} radians\n")
    
    if rmse < 0.05:
        print("✅ ABSOLUTE MATHEMATICAL VALIDATION.")
        print("   Cf is quantitatively equivalent to a standard circular-statistics measure.")
        
    # =========================================================================
    # PART 2: PHASE C EXPORT (Astrophysical Cross-Match)
    # =========================================================================
    print("\n" + "="*80)
    print("PART 2: PHASE C - EXPORTING TARGETS FOR KINEMATIC CROSS-MATCH")
    print("="*80)
    
    os.makedirs('data', exist_ok=True)
    out_csv = 'data/phase_c_crossmatch_targets.csv'
    
    # Export the exact columns Morpheus requested
    export_cols = ['ra_bin', 'dec_bin', 'cf', 'star_count', 'center_ra', 'center_dec']
    res_df[export_cols].sort_values('cf', ascending=False).to_csv(out_csv, index=False)
    
    print(f"💾 Saved full patch footprint to: {out_csv}")
    print("\nNext Step: Cross-match these coordinates against known Galactic streams")
    print("(e.g., Sagittarius, GD-1) and moving groups via SIMBAD and Gaia literature.")
    print("="*80)

if __name__ == "__main__":
    mathematical_closure_and_phase_c()