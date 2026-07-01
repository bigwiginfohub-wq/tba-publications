"""
Filter existing Hyades DR3 catalog for Pleiades members.
Uses Cantat-Gaudin+2022 schema (Cluster ID 20 = Pleiades).
License: CC0 1.0 Universal
"""
import os
import pandas as pd
import numpy as np
from astroquery.vizier import Vizier

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
OUTPUT_FILE = os.path.join(REF_DIR, "pleiades_dr3_high_quality.csv")

# Pleiades Cluster ID in CG22
CLUSTER_ID = 20 
PMEM_THRESHOLD = 0.9

def main():
    print(f"🔭 Downloading Pleiades members from CG22 (Cluster ID {CLUSTER_ID})...")
    
    # We need to download the full table to filter by Cluster ID
    viz = Vizier(columns=["*"], row_limit=-1)
    tables = viz.get_catalogs("J/A+A/658/A41")
    table_key = "J/A+A/658/A41/table2"
    
    if table_key not in tables.keys():
        raise RuntimeError(f"Table {table_key} not found.")
        
    df = tables[table_key].to_pandas()
    
    # Convert masked values
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    # Filter for Pleiades
    if "Cl" not in df.columns:
        # If 'Cl' column doesn't exist, we might need to use spatial coords
        # But CG22 table2 usually has a 'Cl' or 'Cluster' column.
        # If not, we fall back to spatial selection around RA=56.7, Dec=24.1
        print("   ⚠️  No Cluster ID column found. Using spatial selection.")
        from astropy.coordinates import SkyCoord
        import astropy.units as u
        coords = SkyCoord(ra=df["RA_ICRS"].values*u.deg, dec=df["DE_ICRS"].values*u.deg)
        center = SkyCoord(ra=56.7*u.deg, dec=24.1*u.deg)
        sep = coords.separation(center).deg
        df = df[sep < 5.0].copy() # 5 deg radius for Pleiades
    else:
        df = df[df["Cl"] == CLUSTER_ID].copy()
        
    print(f"   Raw Pleiades candidates: {len(df)}")

    # Rename to TRACEBIND schema
    rename_map = {
        "source_id": "source_id", "RA_ICRS": "ra", "DE_ICRS": "dec",
        "Plx": "parallax", "pmRA": "pmra", "pmDE": "pmdec",
        "Gmag": "phot_g_mean_mag", "RUWE": "ruwe",
        "e_Plx": "parallax_error", "e_pmRA": "pmra_error",
        "e_pmDE": "pmdec_error", "Pmem": "member_prob"
    }
    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)
    
    # Apply Quality Filters
    n_before = len(df)
    df = df[df["member_prob"] >= PMEM_THRESHOLD].copy()
    df = df[df["ruwe"] < 1.4].copy()
    df = df[df["parallax"] > 0].copy()
    df = df[df["phot_g_mean_mag"] < 18.0].copy()
    
    # Parallax S/N > 10
    if "parallax_error" in df.columns:
        df = df[df["parallax_error"] > 0].copy()
        df["plx_sn"] = df["parallax"] / df["parallax_error"]
        df = df[df["plx_sn"] > 10].copy()
        
    df = df.dropna(subset=["parallax", "pmra", "pmdec"])
    df = df.reset_index(drop=True)
    
    print(f"   Filtered (Pmem≥{PMEM_THRESHOLD}, RUWE<1.4, Plx S/N>10): {len(df)} members")
    
    # Sanity Check
    med_dist = (1000.0 / df["parallax"]).median()
    print(f"   Median distance: {med_dist:.1f} pc (Expected ~135)")
    
    if med_dist < 100 or med_dist > 180:
        raise RuntimeError(f"Median distance {med_dist:.1f} pc is outside Pleiades range [100, 180] pc.")
        
    os.makedirs(REF_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved Pleiades high-quality subset to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()