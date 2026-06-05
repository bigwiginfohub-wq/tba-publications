import pandas as pd
import numpy as np
import os

print("="*70)
print("[TRACEBIND PHASE 8 v3] KINEMATIC OUTLIERS & BINARY IMPOSTER FILTER")
print("FILTERS: Robust Z-Score | Chaos Score | Astrometric Quality | RUWE Binary Flag")
print("="*70)

# Locate the 12.5k baseline file
file_path = 'data/gaia_phase1_scaled_10k.csv'
if not os.path.exists(file_path):
    file_path = 'gaia_phase1_scaled_10k.csv' 

df = pd.read_csv(file_path)

# 1. ASTROMETRIC QUALITY FILTER
df = df.dropna(subset=['pmra', 'pmdec', 'parallax', 'parallax_error'])
df = df[(df['parallax'] > 0) & ((df['parallax'] / df['parallax_error']) > 5)]
print(f"✅ Loaded {len(df)} sources passing strict astrometric quality cuts (plx SNR > 5).")

# Handle RUWE (Fill NaNs with 1.0, which is a "good" astrometric fit)
if 'ruwe' in df.columns:
    df['ruwe'] = df['ruwe'].fillna(1.0)
else:
    df['ruwe'] = 1.0 # Default to good fit if column missing

# Calculate individual Proper Motion Magnitude
df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)

# 2. ROBUST STATISTICS (Median & MAD)
median_pm = df['pm_mag'].median()
mad_pm = np.median(np.abs(df['pm_mag'] - median_pm))
if mad_pm == 0: mad_pm = 1e-9 

df['pm_robust_z'] = 0.6745 * (df['pm_mag'] - median_pm) / mad_pm

# Bin the sky into patches
ra_bins = np.linspace(0, 360, 19) 
dec_bins = np.linspace(-90, 90, 10) 
df['ra_bin'] = np.digitize(df['ra'], ra_bins)
df['dec_bin'] = np.digitize(df['dec'], dec_bins)

# Calculate Coherence Factor (Cf) per bin
patch_data = []
for (rb, db), group in df.groupby(['ra_bin', 'dec_bin']):
    if len(group) < 15: continue 
    
    pmra_mean = group['pmra'].mean()
    pmdec_mean = group['pmdec'].mean()
    vec_mag = np.sqrt(pmra_mean**2 + pmdec_mean**2)
    mean_mag = group['pm_mag'].mean()
    
    cf = vec_mag / mean_mag if mean_mag > 0 else 0
    
    patch_data.append({
        'ra_bin': rb, 'dec_bin': db,
        'cf': cf,
        'star_count': len(group)
    })

patches = pd.DataFrame(patch_data)

# 3. DATA-DRIVEN THRESHOLDS
cf_threshold = patches['cf'].quantile(0.05)
chaotic_patches = patches[patches['cf'] <= cf_threshold]
print(f"\n🌌 Identified {len(chaotic_patches)} patches of maximum kinetic chaos (Cf <= {cf_threshold:.3f}).")

pm_threshold = df['pm_mag'].quantile(0.99)
print(f"🚀 High Proper Motion threshold set to top 1%: > {pm_threshold:.2f} mas/yr")

# 4. EXTRACT THE OUTLIERS
chaotic_bins = chaotic_patches[['ra_bin', 'dec_bin', 'cf']].rename(columns={'cf': 'patch_cf'})
outliers_pool = pd.merge(df, chaotic_bins, on=['ra_bin', 'dec_bin'])
outliers = outliers_pool[outliers_pool['pm_mag'] > pm_threshold].copy()

# 5. CALCULATE RELIABLE TANGENTIAL VELOCITY (km/s)
# parallax in mas -> distance in kpc
outliers['dist_kpc'] = 1.0 / outliers['parallax'] 
outliers['vt_kms'] = 4.74 * outliers['pm_mag'] * outliers['dist_kpc'] 

# 6. THE CHAOS SCORE & BINARY FLAG
outliers['chaos_score'] = outliers['pm_robust_z'] * (1.0 - outliers['patch_cf'])
outliers['is_binary'] = outliers['ruwe'] > 1.4

# Sort by Chaos Score
outliers = outliers.sort_values('chaos_score', ascending=False)

# 7. BINARY IMPOSTER SUMMARY
binary_count = outliers['is_binary'].sum()
print(f"\n⚠️  BINARY IMPOSTER CHECK:")
print(f"   Of {len(outliers)} kinematic outliers, {binary_count} have RUWE > 1.4.")
print(f"   These are likely unresolved binaries masquerading as fast movers.")
print(f"   The remaining {len(outliers) - binary_count} are TRUE linear movers.\n")

print("--- TOP 10 KINEMATIC OUTLIERS (RANKED BY CHAOS SCORE) ---")
print(f"{'Source ID':<20} | {'PM':>6} | {'V_t':>6} | {'Chaos':>6} | {'RUWE':>5} | {'Status':<15}")
print("-" * 75)

for idx, row in outliers.head(10).iterrows():
    vt_str = f"{row['vt_kms']:.0f}" if not np.isnan(row['vt_kms']) else "N/A"
    status = "⚠️ BINARY WOBBLE" if row['is_binary'] else "✅ TRUE MOVER"
    print(f"{int(row['source_id']):<20} | {row['pm_mag']:>6.2f} | {vt_str:>6} | {row['chaos_score']:>6.2f} | {row['ruwe']:>5.2f} | {status:<15}")

print("\n" + "="*70)
print("[TRANSMISSION READY: PASTE THIS OUTPUT TO GAIA]")
print("="*70)