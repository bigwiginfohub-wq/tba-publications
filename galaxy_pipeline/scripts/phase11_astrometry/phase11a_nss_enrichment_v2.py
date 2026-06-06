import pandas as pd
import numpy as np
from astroquery.gaia import Gaia
from scipy.stats import fisher_exact
import os
import time

def fetch_nss_table(table_name, label):
    """Robustly fetches Gaia tables, falling back to Sync if Async fails."""
    print(f"📡 Downloading {label}...")
    query_async = f"SELECT source_id FROM {table_name}"
    query_sync = f"SELECT TOP 200000 source_id FROM {table_name}"
    
    try:
        # Attempt Async first (best for large tables)
        job = Gaia.launch_job_async(query_async)
        df = job.get_results().to_pandas()
        print(f"✅ Async success: {len(df):,} rows.")
        return df
    except Exception as e:
        print(f"⚠️ Async failed (Server unstable). Falling back to Sync...")
        try:
            time.sleep(2) # Brief pause before retrying
            # Fallback to Sync with a safe TOP limit
            job = Gaia.launch_job(query_sync)
            df = job.get_results().to_pandas()
            print(f"✅ Sync fallback success: {len(df):,} rows (Capped at 200k).")
            return df
        except Exception as e2:
            print(f"❌ Sync also failed. The Gaia Archive is likely offline for DR4 migration.")
            print(f"Error: {e2}")
            return pd.DataFrame(columns=['source_id'])

def run_advanced_nss_enrichment():
    input_file = 'data/phase11a_local_tension_features.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} local targets for Advanced NSS Enrichment.\n")

    # =========================================================================
    # 1. DOWNLOAD GAIA DR3 NSS CATALOGS (With Resilient Fallbacks)
    # =========================================================================
    nss_orbit = fetch_nss_table("gaiadr3.nss_two_body_orbit", "NSS Two Body Orbit")
    nss_accel = fetch_nss_table("gaiadr3.nss_acceleration_astro", "NSS Acceleration Astro")
    
    if nss_orbit.empty and nss_accel.empty:
        print("\n🛑 CRITICAL: Could not download NSS catalogs. The Gaia Archive is completely down.")
        print("Please try again later when the DR4 migration is complete.")
        return

    # =========================================================================
    # 2. MERGE & FEATURE ENGINEERING
    # =========================================================================
    nss_orbit['in_nss_orbit'] = True
    nss_accel['in_nss_accel'] = True
    
    df = df.merge(nss_orbit, on='source_id', how='left')
    df = df.merge(nss_accel, on='source_id', how='left')
    
    df['in_nss_orbit'] = df['in_nss_orbit'].fillna(False)
    df['in_nss_accel'] = df['in_nss_accel'].fillna(False)
    df['in_any_nss'] = df['in_nss_orbit'] | df['in_nss_accel']

    # =========================================================================
    # 3. MEAN TENSION COMPARISON (NSS vs Non-NSS)
    # =========================================================================
    print("\n" + "="*85)
    print("TEST 1: MEAN TENSION SCORE COMPARISON")
    print("="*85)
    mean_tension_nss = df[df['in_any_nss']]['tension_score'].mean()
    mean_tension_non = df[~df['in_any_nss']]['tension_score'].mean()
    
    print(f"Mean Tension (NSS Stars):     {mean_tension_nss:.4f}")
    print(f"Mean Tension (Non-NSS Stars): {mean_tension_non:.4f}")
    
    if mean_tension_nss > mean_tension_non:
        print("✅ NSS stars exhibit higher baseline astrometric tension.")
    else:
        print("⚠️ NSS stars do not exhibit higher baseline tension.")

    # =========================================================================
    # 4. FISHER'S EXACT TEST (Top 50 vs The Rest)
    # =========================================================================
    print("\n" + "="*85)
    print("TEST 2: STATISTICAL SIGNIFICANCE (Fisher's Exact Test)")
    print("="*85)
    
    top50 = df.sort_values('tension_score', ascending=False).head(50)
    rest = df.iloc[50:] 
    
    a = top50['in_any_nss'].sum()           
    b = len(top50) - a                      
    c = rest['in_any_nss'].sum()            
    d = len(rest) - c                       
    
    table = [[a, b], [c, d]]
    oddsratio, pvalue = fisher_exact(table)
    
    print(f"Contingency Table:")
    print(f"             | In NSS | Not NSS |")
    print(f"  Top 50     | {a:>6} | {b:>7} |")
    print(f"  Rest       | {c:>6} | {d:>7} |")
    print(f"\nOdds Ratio: {oddsratio:.2f}")
    print(f"P-value:    {pvalue:.2e}")
    
    if pvalue < 0.01:
        print("✅ HIGHLY SIGNIFICANT (p < 0.01). The Top 50 are statistically enriched for NSS solutions.")
    elif pvalue < 0.05:
        print("⚠️ SIGNIFICANT (p < 0.05). Moderate evidence of enrichment.")
    else:
        print("❌ NOT SIGNIFICANT (p >= 0.05). No statistical evidence of enrichment.")

    # =========================================================================
    # 5. PERCENTILE ENRICHMENT CURVE (Distribution-Independent)
    # =========================================================================
    print("\n" + "="*85)
    print("TEST 3: PERCENTILE ENRICHMENT CURVE")
    print("="*85)
    
    df['pct_bin'] = pd.qcut(df['tension_score'], q=[0, 0.50, 0.90, 0.99, 1.0], labels=['Bottom 50%', '50-90%', '90-99%', 'Top 1%'])
    
    baseline_frac = (df['in_any_nss'].sum() / len(df)) * 100
    
    print(f"{'Percentile Bin':<15} | {'Total Stars':>12} | {'In NSS':>8} | {'NSS Fraction':>12} | {'Enrichment'}")
    print("-" * 75)
    
    for label in ['Bottom 50%', '50-90%', '90-99%', 'Top 1%']:
        subset = df[df['pct_bin'] == label]
        total = len(subset)
        nss_count = subset['in_any_nss'].sum()
        frac = (nss_count / total * 100) if total > 0 else 0
        
        enrichment = frac / baseline_frac if baseline_frac > 0 else 0
        
        print(f"{label:<15} | {total:>12,} | {nss_count:>8} | {frac:>11.2f}% | {enrichment:>5.1f}x baseline")

    # Save enriched catalog
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/phase11a_nss_enriched_v2.csv', index=False)
    print(f"\n💾 Saved V2 enriched catalog to data/phase11a_nss_enriched_v2.csv")
    print("="*85)

if __name__ == "__main__":
    run_advanced_nss_enrichment()