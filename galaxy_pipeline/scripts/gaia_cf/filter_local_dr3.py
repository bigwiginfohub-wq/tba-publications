"""
Filter existing Hyades DR3 catalog for high-quality members.
Uses RUWE < 1.4 and Parallax S/N > 10 as proxies for membership reliability.
License: CC0 1.0 Universal
"""
import os
import pandas as pd
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up TWO levels: gaia_cf -> scripts -> GaiaProject
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))

REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
INPUT_FILE = os.path.join(REF_DIR, "hyades_gaia_dr3.csv")
OUTPUT_FILE = os.path.join(REF_DIR, "hyades_dr3_high_quality.csv")

def main():
    if not os.path.exists(INPUT_FILE):
        raise RuntimeError(f"Input file not found: {INPUT_FILE}")

    print(f"📂 Loading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    print(f"   Found columns: {list(df.columns)}")

    # CRITICAL: Convert all numeric columns to handle CDS masked values ('--')
    numeric_cols = ["parallax", "pmra", "pmdec", "phot_g_mean_mag", "ruwe", 
                    "parallax_error", "pmra_error", "pmdec_error"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Verify required columns exist
    required = {"source_id", "ra", "dec", "parallax", "pmra", "pmdec", 
                "phot_g_mean_mag", "ruwe"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns: {missing}")

    n_before = len(df)
    print(f"   Raw rows: {n_before}")

    # Apply Quality Filters (No member_prob available)
    df_filtered = df[df["ruwe"] < 1.4].copy()
    df_filtered = df_filtered[df_filtered["parallax"] > 0].copy()
    df_filtered = df_filtered[df_filtered["phot_g_mean_mag"] < 18.0].copy()
    
    # Filter by Parallax S/N > 10 (High precision distance)
    if "parallax_error" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["parallax_error"] > 0].copy()
        df_filtered["plx_sn"] = df_filtered["parallax"] / df_filtered["parallax_error"]
        df_filtered = df_filtered[df_filtered["plx_sn"] > 10].copy()
        print("   Applied filter: Parallax S/N > 10")
    else:
        print("   ⚠️  No parallax_error column found. Skipping S/N filter.")

    # Drop any remaining NaNs in critical astrometric columns
    df_filtered = df_filtered.dropna(subset=["parallax", "pmra", "pmdec"])
    df_filtered = df_filtered.reset_index(drop=True)
    
    n_after = len(df_filtered)
    print(f"   Filtered (RUWE<1.4, G<18, Plx S/N>10): {n_after} members")

    # Sanity Checks
    if n_after == 0:
        raise RuntimeError("No members passed the filters. Check input data quality.")
        
    # Diagnostic Output
    med_dist = (1000.0 / df_filtered["parallax"]).median()
    med_ruwe = df_filtered["ruwe"].median()
    
    print(f"\n📊 High-Quality Subset Diagnostics:")
    print(f"   Median distance: {med_dist:.1f} pc (Expected ~47)")
    print(f"   Median RUWE:     {med_ruwe:.3f}")

    if med_dist < 30 or med_dist > 60:
        raise RuntimeError(f"Median distance {med_dist:.1f} pc is outside Hyades range [30, 60] pc.")

    # Save
    os.makedirs(REF_DIR, exist_ok=True)
    df_filtered.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved high-quality subset to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()