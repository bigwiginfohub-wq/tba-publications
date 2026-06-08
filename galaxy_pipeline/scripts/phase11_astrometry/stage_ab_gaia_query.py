import os
import numpy as np
import pandas as pd
from astroquery.gaia import Gaia

def query_astrometric_tension_features():
    print("="*85)
    print("TRACEBIND PHASE 11A: ASTROMETRIC QUALITY & TENSION FEATURE EXTRACTION")
    print("="*85)
    
    # Morpheus Fix: Removed arbitrary TOP 5000. 
    # Added TOP 200000 to prevent ADQL timeout while capturing the full local census.
    # Added BP/RP mags, Radial Velocity, and duplicated_source flag.
    query = """
    SELECT TOP 200000
        source_id, ra, dec,
        parallax, parallax_error,
        pmra, pmra_error, pmdec, pmdec_error,
        ruwe, 
        astrometric_excess_noise,
        visibility_periods_used,
        phot_g_mean_mag,
        bp_rp,
        phot_bp_mean_mag,
        phot_rp_mean_mag,
        phot_bp_rp_excess_factor,
        radial_velocity,
        radial_velocity_error,
        duplicated_source,
        teff_gspphot
    FROM gaiadr3.gaia_source
    WHERE parallax > 20.0             -- Within 50 parsecs
      AND parallax_error > 0
      AND (parallax / parallax_error) > 10  -- 10% distance precision
      AND visibility_periods_used >= 12     -- Good scan coverage
      AND phot_g_mean_mag < 15.0            -- Bright enough for high precision
    ORDER BY parallax DESC
    """
    
    print("📡 Querying Gaia DR3 for local solar neighborhood astrometry...")
    job = Gaia.launch_job(query)
    results = job.get_results()
    
    df = results.to_pandas()
    print(f"✅ Retrieved {len(df)} local stars.\n")
    
    # -------------------------------------------------------------------------
    # FEATURE ENGINEERING (Morpheus Corrections Applied)
    # -------------------------------------------------------------------------
    
    # 1. Basic Astrometric Derivations
    df['plx_snr'] = df['parallax'] / df['parallax_error']
    df['pm_tot'] = np.sqrt(df['pmra']**2 + df['pmdec']**2)
    
    # 2. Tangential Velocity (vt = 4.74047 * mu[arcsec/yr] * d[pc])
    # pm_tot is in mas/yr (divide by 1000). Distance is 1000/parallax.
    # The 1000s cancel out, leaving: 4.74047 * pm_tot / parallax
    df['vt_kms'] = 4.74047 * df['pm_tot'] / df['parallax']
    
    # 3. Continuous Tension Scoring (Replacing Boolean Flags)
    # We use log10 to compress the dynamic range and handle extreme outliers gracefully.
    # Clip lower bounds to prevent log10(0) or negative errors.
    df['log_ruwe'] = np.log10(df['ruwe'].clip(lower=0.1))
    df['log_noise'] = np.log10(1 + df['astrometric_excess_noise'].clip(lower=0))
    
    # The Composite Tension Score
    df['tension_score'] = df['log_ruwe'] + df['log_noise']
    
    # -------------------------------------------------------------------------
    # SUMMARY STATISTICS
    # -------------------------------------------------------------------------
    print("--- ASTROMETRIC MODEL TENSION SUMMARY ---")
    print(f"Total Local Targets:    {len(df)}")
    print(f"Mean Tangential Vel:    {df['vt_kms'].mean():.2f} km/s")
    print(f"Mean Tension Score:     {df['tension_score'].mean():.3f}")
    print(f"Max Tension Score:      {df['tension_score'].max():.3f} (Highest model failure)")
    
    # Identify stars with severe single-star model tension
    # (e.g., tension_score > 0.5 implies RUWE > ~2.0 and/or significant excess noise)
    high_tension = df[df['tension_score'] > 0.5]
    print(f"\n⚠️ High Astrometric Model Tension (Score > 0.5): {len(high_tension)} stars")
    print("   (These indicate the Gaia single-star solution is imperfect.")
    print("    Causes remain unknown until HGCA PMa and cross-matches are added.)")
    
    # -------------------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------------------
    os.makedirs('data', exist_ok=True)
    out_file = 'data/phase11a_local_tension_features.csv'
    
    # Sort by tension score descending so the most interesting anomalies are at the top
    df = df.sort_values('tension_score', ascending=False)
    df.to_csv(out_file, index=False)
    
    print(f"\n💾 Saved Phase 11A feature matrix to {out_file}")
    print("="*85)
    print("NEXT STEP (Phase 11B): Cross-match source_ids with the HGCA catalog")
    print("to compute Proper Motion Anomaly (PMa) significance.")
    print("="*85)

if __name__ == "__main__":
    query_astrometric_tension_features()