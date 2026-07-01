import pandas as pd
import numpy as np
import os

print("="*70)
print("[TRACEBIND] MILKY WAY KINEMATIC COHERENCE AUDIT")
print("="*70)

# Locate the 12.5k baseline file
file_path = 'data/gaia_phase1_scaled_10k.csv'
if not os.path.exists(file_path):
    file_path = 'gaia_phase1_scaled_10k.csv' # Fallback if not moved to /data

df = pd.read_csv(file_path)

# Drop rows missing proper motion data
df = df.dropna(subset=['pmra', 'pmdec'])
print(f"✅ Loaded {len(df)} sources with proper motion telemetry.")

# 1. COORDINATE RANGE (The Spatial Footprint)
print("\n--- SPATIAL FOOTPRINT BOUNDARIES ---")
print(f"Right Ascension (RA) Range:  {df['ra'].min():.4f} to {df['ra'].max():.4f} deg")
print(f"Declination (Dec) Range:     {df['dec'].min():.4f} to {df['dec'].max():.4f} deg")

# 2. CALCULATE PROPER MOTION COHERENCE (Cf) PER PATCH
# We bin the sky into a grid (approx 30x30 degree patches)
ra_bins = np.linspace(0, 360, 13) 
dec_bins = np.linspace(-90, 90, 7) 

df['ra_bin'] = np.digitize(df['ra'], ra_bins)
df['dec_bin'] = np.digitize(df['dec'], dec_bins)

print("\n--- CALCULATING COHERENCE FACTOR (Cf) ---")
print("Formula: Cf = |Mean Vector| / Mean(Magnitudes)")
print("1.0 = Perfect Stream Alignment | 0.0 = Random Kinetic Noise\n")

results = []
for (rb, db), group in df.groupby(['ra_bin', 'dec_bin']):
    if len(group) < 15: # Require a minimum density to measure coherence
        continue
    
    # Mean Vector Components
    pmra_mean = group['pmra'].mean()
    pmdec_mean = group['pmdec'].mean()
    vec_mag = np.sqrt(pmra_mean**2 + pmdec_mean**2)
    
    # Individual Magnitudes
    mags = np.sqrt(group['pmra']**2 + group['pmdec']**2)
    mean_mag = mags.mean()
    
    # Coherence Factor
    cf = vec_mag / mean_mag if mean_mag > 0 else 0
    
    results.append({
        'ra_center': group['ra'].mean(),
        'dec_center': group['dec'].mean(),
        'star_count': len(group),
        'coherence_cf': cf,
        'mean_pmra': pmra_mean,
        'mean_pmdec': pmdec_mean,
        'mean_pm_mag': mean_mag
    })

res_df = pd.DataFrame(results)
res_df = res_df.sort_values('coherence_cf', ascending=False)

print("--- TOP 5 HIGH-COHERENCE KINEMATIC PATCHES ---")
# Print cleanly for the transmission
for idx, row in res_df.head(5).iterrows():
    print(f"PATCH | RA: {row['ra_center']:>7.2f} | Dec: {row['dec_center']:>7.2f} | "
          f"Stars: {int(row['star_count']):>4} | Cf: {row['coherence_cf']:.4f} | "
          f"Vector: ({row['mean_pmra']:.2f}, {row['mean_pmdec']:.2f}) mas/yr")

print("\n" + "="*70)
print("[TRANSMISSION READY FOR GAIA ARCHIVE]")
print("="*70)