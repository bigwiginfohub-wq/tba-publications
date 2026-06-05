import pandas as pd
import numpy as np
import os
from astropy.coordinates import SkyCoord
import astropy.units as u

def run_phase_d_master_test():
    input_file = 'data/gaia_phase1_scaled_10k.csv'
    if not os.path.exists(input_file):
        input_file = 'gaia_phase1_scaled_10k.csv'
        
    df = pd.read_csv(input_file)
    df = df.dropna(subset=['ra', 'dec', 'pmra', 'pmdec', 'parallax', 'parallax_error'])
    
    # Strict cuts for reliable distances
    df = df[df['parallax'] > 0]
    df = df[(df['parallax'] / df['parallax_error']) > 5] 
    df['dist_pc'] = 1000.0 / df['parallax']
    df['dist_kpc'] = df['dist_pc'] / 1000.0
    df = df[df['dist_kpc'] < 15.0] 
    
    print(f"📋 Loaded {len(df)} sources for Phase D Master Test.\n")

    # 1. TRANSFORM TO GALACTIC FRAME
    print("🌌 Transforming to Galactic Coordinates (l, b, mu_l, mu_b)...")
    c = SkyCoord(ra=df['ra'].values*u.deg, dec=df['dec'].values*u.deg,
                 pm_ra_cosdec=df['pmra'].values*u.mas/u.yr, pm_dec=df['pmdec'].values*u.mas/u.yr,
                 distance=df['dist_pc'].values*u.pc, frame='icrs')
    
    gal = c.galactic
    l_rad = gal.l.rad
    b_rad = gal.b.rad
    obs_mu_l = gal.pm_l_cosb.value  
    obs_mu_b = gal.pm_b.value       

    # 2. SUBTRACT FIRST-ORDER GALACTIC ROTATION (Oort Constants)
    A, B = 15.3, -11.9 # km/s/kpc
    v_l_oort = df['dist_kpc'].values * (A * np.cos(2 * l_rad) + B)
    v_b_oort = -df['dist_kpc'].values * A * np.sin(2 * l_rad) * np.sin(b_rad)
    mu_l_oort = v_l_oort / 4.74047
    mu_b_oort = v_b_oort / 4.74047

    # 3. SUBTRACT SOLAR REFLEX MOTION (Schönrich et al. 2010)
    # The Sun moves at (U, V, W). The "reflex" is how that makes stars APPEAR to move.
    U_sun, V_sun, W_sun = 11.1, 12.24, 7.25 # km/s
    v_l_sun = U_sun * np.sin(l_rad) - V_sun * np.cos(l_rad)
    v_b_sun = (U_sun * np.cos(l_rad) * np.sin(b_rad) + 
               V_sun * np.sin(l_rad) * np.sin(b_rad) - 
               W_sun * np.cos(b_rad))
    mu_l_sun = v_l_sun / (4.74047 * df['dist_kpc'].values)
    mu_b_sun = v_b_sun / (4.74047 * df['dist_kpc'].values)

    # Total Expected Background = Oort + Solar Reflex
    mu_l_exp = mu_l_oort + mu_l_sun
    mu_b_exp = mu_b_oort + mu_b_sun
    
    # Residual Proper Motions
    res_mu_l = obs_mu_l - mu_l_exp
    res_mu_b = obs_mu_b - mu_b_exp
    
    res_pm_mag = np.sqrt(res_mu_l**2 + res_mu_b**2)
    valid_mask = res_pm_mag > 0.05 
    
    l_rad, b_rad = l_rad[valid_mask], b_rad[valid_mask]
    res_ux = res_mu_l[valid_mask] / res_pm_mag[valid_mask]
    res_uy = res_mu_b[valid_mask] / res_pm_mag[valid_mask]
    
    df_res = pd.DataFrame({'l': np.degrees(l_rad), 'b': np.degrees(b_rad), 'ux': res_ux, 'uy': res_uy})
    print(f"✅ Subtracted Oort + Solar Reflex. {len(df_res)} residual vectors remain.\n")

    # 4. BINNING & METRICS
    l_bins = np.linspace(0, 360, 13)
    b_bins = np.linspace(-90, 90, 7)
    df_res['l_bin'] = np.digitize(df_res['l'], l_bins)
    df_res['b_bin'] = np.digitize(df_res['b'], b_bins)
    
    valid_groups = {idx: grp.values for idx, grp in df_res.groupby(['l_bin', 'b_bin']).groups.items() if len(grp) >= 20}

    def calculate_metrics(ux_arr, uy_arr):
        cfs = [np.sqrt(np.mean(ux_arr[g])**2 + np.mean(uy_arr[g])**2) for g in valid_groups.values()]
        cfs = np.sort(np.array(cfs))
        if len(cfs) == 0: return {'max': 0, 'mean': 0, 'p95': 0, 'top5_mean': 0}
        return {
            'max': cfs[-1], 'mean': np.mean(cfs), 'p95': np.percentile(cfs, 95),
            'top5_mean': np.mean(cfs[-5:]) if len(cfs) >= 5 else np.mean(cfs)
        }

    # 5. OBSERVED & NULL DISTRIBUTIONS
    obs_metrics = calculate_metrics(df_res['ux'].values, df_res['uy'].values)
    
    print("="*85)
    print("PART 1: OBSERVED RESIDUAL SKY (Oort + Solar Reflex Subtracted)")
    print("="*85)
    for k, v in obs_metrics.items(): print(f"  {k:<12}: {v:.4f}")

    print("\n" + "="*85)
    print("PART 2: RESIDUAL PERMUTATION TEST (1,000 Shuffled Skies)")
    print("="*85)
    np.random.seed(42)
    null_dist = {'max': [], 'mean': [], 'p95': [], 'top5_mean': []}
    ux_vals, uy_vals = df_res['ux'].values, df_res['uy'].values
    
    for i in range(1000):
        shuf = np.random.permutation(len(df_res))
        shuf_metrics = calculate_metrics(ux_vals[shuf], uy_vals[shuf])
        for k in null_dist: null_dist[k].append(shuf_metrics[k])
        if (i + 1) % 250 == 0: print(f"  Completed {i+1}/1000 permutations...")

    for k in null_dist: null_dist[k] = np.array(null_dist[k])

    # 6. STATISTICAL SIGNIFICANCE
    print("\n" + "="*85)
    print("PART 3: SUBSTRUCTURE SIGNIFICANCE (Background Subtracted)")
    print("="*85)
    print(f"{'Metric':<12} | {'Observed':>8} | {'Null Mean':>9} | {'Null Max':>8} | {'p-value':>8} | {'Z-Score':>8}")
    print("-" * 75)
    
    for k in ['max', 'mean', 'p95', 'top5_mean']:
        obs, null = obs_metrics[k], null_dist[k]
        p = np.sum(null >= obs) / 1000
        z = (obs - np.mean(null)) / np.std(null) if np.std(null) > 0 else 0
        print(f"{k:<12} | {obs:>8.4f} | {np.mean(null):>9.4f} | {np.max(null):>8.4f} | {p:>8.4f} | {z:>+8.2f}")

    os.makedirs('data', exist_ok=True)
    pd.DataFrame(null_dist).to_csv('data/phase_d_residual_null_distribution.csv', index=False)
    
    # 7. MORPHEUS-APPROVED VERDICT
    print("\n" + "="*85)
    print("FINAL REFEREE-PROOF VERDICT")
    print("="*85)
    p_mean = np.sum(null_dist['mean'] >= obs_metrics['mean']) / 1000
    
    if p_mean < 0.01:
        print("✅ PUBLISHABLE EMPIRICAL STATEMENT ACHIEVED (p < 0.01)")
        print("   Residual directional coherence remains significantly above randomized")
        print("   expectations after subtraction of a first-order Galactic rotation model")
        print("   and solar reflex motion.")
    else:
        print("❌ SIGNAL EXPLAINED BY BACKGROUND KINEMATICS")
        print("   Once Oort shear and solar reflex are removed, the residual sky is")
        print("   statistically indistinguishable from random noise.")
    print("="*85)

if __name__ == "__main__":
    run_phase_d_master_test()