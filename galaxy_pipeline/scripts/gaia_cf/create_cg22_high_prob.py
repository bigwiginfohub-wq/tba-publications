"""
Create High-Probability Cantat-Gaudin 2022 Hyades Catalog
Source: J/A+A/658/A41/table2 (Gaia DR3)
Filter: Pmem >= 0.9, RUWE < 1.4, G < 18
License: CC0 1.0 Universal
"""
import os
import pandas as pd
import numpy as np
from astroquery.vizier import Vizier

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
OUTPUT_FILE = os.path.join(REF_DIR, "hyades_cg22_pmem90.csv")

CATALOG_ID = "J/A+A/658/A41"
TABLE_KEY = "J/A+A/658/A41/table2"
PMEM_THRESHOLD = 0.9

def main():
    print(f"🔭 Downloading {CATALOG_ID}/table2 from VizieR...")
    
    # Configure Vizier to get all columns and no row limit
    viz = Vizier(columns=["*"], row_limit=-1)
    
    try:
        tables = viz.get_catalogs(CATALOG_ID)
        
        if TABLE_KEY not in tables.keys():
            raise RuntimeError(f"Table {TABLE_KEY} not found. Available: {list(tables.keys())}")
            
        df = tables[TABLE_KEY].to_pandas()
        print(f"   Raw rows downloaded: {len(df)}")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return

    # CRITICAL: Convert CDS masked values ('--', '---') to NaN
    # This prevents negative numbers from being treated as valid astrometry
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    # Rename to TRACEBIND internal schema
    rename_map = {
        "source_id": "source_id",
        "RA_ICRS": "ra",
        "DE_ICRS": "dec",
        "Plx": "parallax",
        "pmRA": "pmra",
        "pmDE": "pmdec",
        "Gmag": "phot_g_mean_mag",
        "RUWE": "ruwe",
        "e_Plx": "parallax_error",
        "e_pmRA": "pmra_error",
        "e_pmDE": "pmdec_error",
        "Pmem": "member_prob"
    }
    # Only rename columns that actually exist in the downloaded table
    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)
    
    # Verify required columns
    required = {"source_id", "ra", "dec", "parallax", "pmra", "pmdec", 
                "phot_g_mean_mag", "ruwe", "member_prob"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns after rename: {missing}")
        
    # Apply filters
    n_before = len(df)
    
    # 1. Membership Probability
    df = df[df["member_prob"] >= PMEM_THRESHOLD].copy()
    
    # 2. Astrometric Quality (RUWE)
    df = df[df["ruwe"] < 1.4].copy()
    
    # 3. Valid Parallax
    df = df[df["parallax"] > 0].copy()
    
    # 4. Magnitude Limit
    df = df[df["phot_g_mean_mag"] < 18.0].copy()
    
    # 5. Remove any remaining NaNs in critical columns
    df = df.dropna(subset=["parallax", "pmra", "pmdec"])
    
    df = df.reset_index(drop=True)
    
    print(f"   Filters applied (Pmem≥{PMEM_THRESHOLD}, RUWE<1.4, G<18): {n_before} → {len(df)}")
    
    # Sanity Checks
    if len(df) < 100:
        raise RuntimeError(f"Only {len(df)} members passed cuts. Expected >100.")
        
    med_dist = (1000.0 / df["parallax"]).median()
    if med_dist < 30 or med_dist > 60:
        raise RuntimeError(f"Median distance {med_dist:.1f} pc is outside Hyades range [30, 60] pc.")
        
    # Save
    os.makedirs(REF_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved {len(df)} high-probability members to {OUTPUT_FILE}")
    print(f"   Median distance: {med_dist:.1f} pc")
    print(f"   Median RUWE: {df['ruwe'].median():.3f}")

if __name__ == "__main__":
    main()