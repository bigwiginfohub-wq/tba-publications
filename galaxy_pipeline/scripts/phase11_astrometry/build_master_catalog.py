import pandas as pd
import numpy as np
import os
from astropy.coordinates import SkyCoord
import astropy.units as u

def build_master_catalog():
    # We start from the NSS-enriched catalog, which already has tension scores and NSS flags
    input_file = 'data/phase11a_nss_enriched_v2.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    print("📥 Loading Phase 11A NSS-Enriched Data...")
    df = pd.read_csv(input_file)
    print(f"✅ Loaded {len(df):,} sources.\n")

    print("⚙️ FORGING MASTER CATALOG: Computing Derived Physical Parameters...")
    
    # 1. Ensure Core Astrometry is Numeric
    for col in ['ra', 'dec', 'parallax', 'phot_g_mean_mag', 'phot_bp_mean_mag', 'phot_rp_mean_mag']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. Compute BP-RP Color (Robust fallback if Gaia's bp_rp column is missing/NaN)
    if 'bp_rp' not in df.columns or df['bp_rp'].isna().sum() > len(df) * 0.5:
        if 'phot_bp_mean_mag' in df.columns and 'phot_rp_mean_mag' in df.columns:
            df['bp_rp'] = df['phot_bp_mean_mag'] - df['phot_rp_mean_mag']
            print("   -> Computed bp_rp from BP and RP magnitudes.")

    # 3. Compute Distance (pc)
    df['distance_pc'] = 1000.0 / df['parallax']
    
    # 4. Compute Absolute Magnitude (M_G)
    # M_G = G - 5*log10(d) + 5
    df['M_G'] = df['phot_g_mean_mag'] - 5 * np.log10(df['distance_pc']) + 5
    print("   -> Computed Absolute Magnitude (M_G).")

    # 5. Compute Galactic Coordinates (l, b)
    coords = SkyCoord(ra=df['ra'].values * u.deg, dec=df['dec'].values * u.deg, frame='icrs')
    df['gal_l'] = coords.galactic.l.deg
    df['gal_b'] = coords.galactic.b.deg
    print("   -> Computed Galactic Coordinates (l, b).")

    # 6. Compute Tangential Velocity (km/s)
    df['pm_tot'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    df['vt_kms'] = 4.74047 * df['pm_tot'] / df['parallax']
    print("   -> Computed Tangential Velocity (vt_kms).")

    # 7. Apply Anomaly Classification (From Benchmark Generator)
    def classify_anomaly(row):
        if row.get('in_nss_orbit', False): return 'Known NSS Orbit (Binary/Multiple)'
        if row.get('in_nss_accel', False): return 'NSS Acceleration (PMa / Unseen Companion)'
        if row['phot_g_mean_mag'] < 6.0: return 'Bright Star Artifact Suspect (G < 6)'
        if row['phot_g_mean_mag'] > 14.5: return 'Faint Star Noise Suspect (G > 14.5)'
        return 'Unexplained Astrometric Tension (High Priority)'

    # Apply only to the top 5% tension to match the benchmark catalog logic
    threshold = np.percentile(df['tension_score'], 95)
    df['anomaly_class'] = 'Below Top 5% Threshold'
    
    high_tension_mask = df['tension_score'] >= threshold
    df.loc[high_tension_mask, 'anomaly_class'] = df[high_tension_mask].apply(classify_anomaly, axis=1)
    print("   -> Applied Anomaly Classification.")

    # 8. Drop rows with critical NaNs for the HR diagram and spatial plots
    initial_count = len(df)
    df = df.dropna(subset=['ra', 'dec', 'distance_pc', 'M_G', 'bp_rp', 'tension_score'])
    print(f"   -> Dropped {initial_count - len(df)} rows with missing critical photometry/astrometry.")

    # =========================================================================
    # EXPORT THE CANONICAL MASTER CATALOG
    # =========================================================================
    out_file = 'data/tracebind_master_catalog_v1.csv'
    df.to_csv(out_file, index=False)
    
    print("\n" + "="*85)
    print("✅ TRACEBIND MASTER CATALOG V1.0 FORGED.")
    print(f"💾 Saved to: {out_file}")
    print(f"📊 Total Rows: {len(df):,}")
    print(f"🎯 High-Tension Anomalies: {(df['anomaly_class'] != 'Below Top 5% Threshold').sum():,}")
    print("="*85)
    print("\nAll future plotting, cross-matching, and DR4 prediction scripts")
    print("must now read exclusively from this Master Catalog.")
    print("="*85)

if __name__ == "__main__":
    build_master_catalog()