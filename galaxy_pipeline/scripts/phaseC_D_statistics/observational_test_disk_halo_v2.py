import pandas as pd
import numpy as np
import os
from astropy.coordinates import SkyCoord
import astropy.units as u

def test_disk_vs_halo_coherence_v2():
    input_file = 'data/gaia_phase1_scaled_10k.csv'
    if not os.path.exists(input_file):
        input_file = 'gaia_phase1_scaled_10k.csv'
        
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    df = df.dropna(subset=['ra', 'dec', 'pmra', 'pmdec'])
    
    # Calculate PM magnitude to filter out stationary/noisy sources and create unit vectors
    df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    df = df[df['pm_mag'] > 0.1] # Require some measurable motion
    
    print(f"📋 Loaded {len(df)} sources with measurable proper motion.\n")

    # 1. CONVERT TO GALACTIC COORDINATES (l, b)
    print("🌌 Converting Equatorial (RA/Dec) to Galactic (l, b) coordinates...")
    coords = SkyCoord(ra=df['ra'].values * u.deg, 
                      dec=df['dec'].values * u.deg, 
                      frame='icrs')
    
    df['l'] = coords.galactic.l.deg
    df['b'] = coords.galactic.b.deg
    df['abs_b'] = np.abs(df['b'])

    # 2. CREATE 2D GALACTIC BINS (Reviewer's Fix for Vector Cancellation)
    # 12 bins in longitude (30 deg each), 18 bins in latitude (10 deg each)
    l_bins = np.linspace(0, 360, 13)
    b_bins = np.linspace(-90, 90, 19)
    
    df['l_bin'] = np.digitize(df['l'], l_bins)
    df['b_bin'] = np.digitize(df['b'], b_bins)

    # 3. CALCULATE LOCAL 2D COHERENCE WITH BOOTSTRAPPING
    print("⏳ Calculating local 2D coherence (Unit Vectors) with Bootstrapping...")
    local_results = []
    
    for (l_b, b_b), group in df.groupby(['l_bin', 'b_bin']):
        if len(group) < 20:  # Require statistical significance per 2D patch
            continue
            
        # Unit vectors (direction only, stripping away amplitude dominance)
        ux = group['pmra'].values / group['pm_mag'].values
        uy = group['pmdec'].values / group['pm_mag'].values
        
        # Bootstrap for uncertainty estimation (100 iterations for speed)
        np.random.seed(42) # For reproducibility
        boot_cfs = []
        for _ in range(100):
            idx = np.random.choice(len(group), size=len(group), replace=True)
            mean_ux = np.mean(ux[idx])
            mean_uy = np.mean(uy[idx])
            cf_boot = np.sqrt(mean_ux**2 + mean_uy**2)
            boot_cfs.append(cf_boot)
            
        local_results.append({
            'l_bin': l_b,
            'b_bin': b_b,
            'abs_b_center': np.abs(group['b'].mean()),
            'star_count': len(group),
            'cf_mean': np.mean(boot_cfs),
            'cf_std': np.std(boot_cfs)
        })

    local_df = pd.DataFrame(local_results)

    # 4. AGGREGATE BY ABSOLUTE LATITUDE (The Disk-to-Halo Gradient)
    # 10 edges = 9 bins (0-10, 10-20 ... 80-90)
    abs_b_bands = np.linspace(0, 90, 10) 
    
    # FIX: Clip digitize to prevent bin 10 (values exactly at 90.0)
    local_df['abs_b_band'] = np.clip(
        np.digitize(local_df['abs_b_center'], abs_b_bands),
        1,
        len(abs_b_bands) - 1
    )
    
    # FIX: Safe label generation (9 bins)
    band_labels = {}
    for i in range(len(abs_b_bands) - 1):
        band_labels[i + 1] = f"{abs_b_bands[i]:.0f}°-{abs_b_bands[i+1]:.0f}°"

    final_gradient = []
    for band_id, band_group in local_df.groupby('abs_b_band'):
        # Weighted average of local coherence by star count
        w = band_group['star_count']
        cf_weighted = np.average(band_group['cf_mean'], weights=w)
        cf_err = np.average(band_group['cf_std'], weights=w) / np.sqrt(len(band_group)) # Error of the mean
        
        final_gradient.append({
            'lat_range': band_labels.get(band_id, 'Unknown'),
            'patches': len(band_group),
            'total_stars': band_group['star_count'].sum(),
            'cf_gradient': cf_weighted,
            'cf_error': cf_err
        })

    grad_df = pd.DataFrame(final_gradient)

    # 5. PRINT THE OBSERVATIONAL TRUTH
    print("\n" + "="*85)
    print("      OBSERVATIONAL TEST: LOCAL KINEMATIC COHERENCE vs. GALACTIC STRUCTURE")
    print("="*85)
    print("Hypothesis: The Disk (|b| ≈ 0°) should have HIGH local coherence (ordered flows).")
    print("            The Halo (|b| → 90°) should have LOW local coherence (chaotic orbits).\n")
    
    print(f"{'Lat Range':<12} | {'Patches':>7} | {'Stars':>7} | {'Local Cf (± σ)':>16} | {'Structure Interpretation'}")
    print("-" * 85)
    
    for idx, row in grad_df.iterrows():
        cf = row['cf_gradient']
        err = row['cf_error']
        if cf > 0.60:
            interp = "✅ HIGHLY ORDERED (Spiral Arm / Disk Flow)"
        elif cf > 0.35:
            interp = "⚠️ MODERATE (Transition Zone / Thick Disk)"
        else:
            interp = "❌ CHAOTIC (Stellar Halo / Merger Debris)"
            
        print(f"{row['lat_range']:<12} | {int(row['patches']):>7} | {int(row['total_stars']):>7} | {cf:.3f} ± {err:.3f}    | {interp}")

    # 6. STATISTICAL CORRELATION
    # Extract the lower bound of the latitude range for correlation math
    grad_df['lat_lower_bound'] = grad_df['lat_range'].apply(lambda x: float(x.split('°')[0]))
    corr = grad_df['lat_lower_bound'].corr(grad_df['cf_gradient'])
    
    print("\n" + "="*85)
    print(f"Observed Correlation (Absolute Galactic Latitude vs Local Cf): r = {corr:.3f}")
    print("="*85)
    print("Note: A negative correlation indicates that kinematic coherence successfully")
    print("traces the transition from the ordered Galactic Disk to the chaotic Halo.")
    print("="*85)

if __name__ == "__main__":
    test_disk_vs_halo_coherence_v2()