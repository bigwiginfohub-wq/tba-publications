import pandas as pd
import numpy as np
import os

print("="*70)
print("[TRACEBIND PHASE 9] ALL-SKY EQUAL-AREA COHERENCE MAPPING")
print("TARGET: Mapping the Kinematic Skeleton of the Milky Way")
print("="*70)

# Attempt to import healpy. If it fails, use the math-based equal-area fallback.
try:
    import healpy as hp
    USE_HEALPIX = True
    print("✅ Using HEALPix (Industry Standard Equal-Area Pixelation)")
except ImportError:
    USE_HEALPIX = False
    print("⚠️ healpy not found. Using Sine-Declination Equal-Area Fallback.")
    print("   (To install native HEALPix, run: pip install healpy)")

# Locate the 12.5k baseline file
file_path = 'data/gaia_phase1_scaled_10k.csv'
if not os.path.exists(file_path):
    file_path = 'gaia_phase1_scaled_10k.csv' 

df = pd.read_csv(file_path)
df = df.dropna(subset=['pmra', 'pmdec'])
print(f"✅ Loaded {len(df)} sources with proper motion telemetry.\n")

# Calculate individual Proper Motion Magnitude
df['pm_mag'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)

# Calculate Coherence Factor (Cf)
def calculate_cf(group):
    if len(group) < 10: # Minimum stars per pixel to measure coherence
        return pd.Series({'cf': np.nan, 'star_count': len(group), 'mean_pm': np.nan})
    
    pmra_mean = group['pmra'].mean()
    pmdec_mean = group['pmdec'].mean()
    vec_mag = np.sqrt(pmra_mean**2 + pmdec_mean**2)
    mean_mag = group['pm_mag'].mean()
    
    cf = vec_mag / mean_mag if mean_mag > 0 else 0
    return pd.Series({'cf': cf, 'star_count': len(group), 'mean_pm': mean_mag})

if USE_HEALPIX:
    NSIDE = 32 # ~12,288 pixels across the whole sky
    theta = np.radians(90.0 - df['dec']) # Colatitude
    phi = np.radians(df['ra'])           # Longitude
    df['pixel_id'] = hp.ang2pix(NSIDE, theta, phi, nest=False)
else:
    # Equal-Area Cylindrical Fallback: Bin by RA and sin(Dec)
    # This guarantees every bin covers the exact same solid angle on the sky
    ra_bins = np.linspace(0, 360, 25)
    sin_dec_bins = np.linspace(-1, 1, 19) # sin(-90) to sin(90)
    
    df['ra_bin'] = np.digitize(df['ra'], ra_bins)
    df['sin_dec_bin'] = np.digitize(np.sin(np.radians(df['dec'])), sin_dec_bins)
    # Combine into a single pixel ID
    df['pixel_id'] = df['ra_bin'] * 100 + df['sin_dec_bin']

# Group by pixel and calculate Cf
print("⏳ Calculating Coherence Factor (Cf) across the sky...")
sky_map = df.groupby('pixel_id').apply(calculate_cf).reset_index()
sky_map = sky_map.dropna(subset=['cf'])

# Sort by Coherence to find the great galactic currents
sky_map = sky_map.sort_values('cf', ascending=False)

print(f"\n🌌 Mapped {len(sky_map)} valid equal-area sky pixels (min 10 stars/pixel).")

print("\n--- TOP 10 HIGH-COHERENCE KINEMATIC CURRENTS (The Spiral Arms & Streams) ---")
print(f"{'Pixel ID':<10} | {'Stars':>6} | {'Coherence (Cf)':>14} | {'Mean PM (mas/yr)':>16}")
print("-" * 55)
for idx, row in sky_map.head(10).iterrows():
    print(f"{int(row['pixel_id']):<10} | {int(row['star_count']):>6} | {row['cf']:>14.4f} | {row['mean_pm']:>16.2f}")

print("\n--- TOP 10 MAXIMUM CHAOS ZONES (The Halo & Inter-Arm Voids) ---")
print(f"{'Pixel ID':<10} | {'Stars':>6} | {'Coherence (Cf)':>14} | {'Mean PM (mas/yr)':>16}")
print("-" * 55)
for idx, row in sky_map.tail(10).iterrows():
    print(f"{int(row['pixel_id']):<10} | {int(row['star_count']):>6} | {row['cf']:>14.4f} | {row['mean_pm']:>16.2f}")

# Save the map
output_file = 'data/phase9_allsky_coherence_map.csv'
os.makedirs('data', exist_ok=True)
sky_map.to_csv(output_file, index=False)
print(f"\n💾 Saved All-Sky Coherence Map to {output_file}")
print("="*70)