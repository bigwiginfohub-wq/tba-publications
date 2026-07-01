"""
Fetch a specific open cluster from Cantat-Gaudin+2022 via Gaia Archive ADQL.
Bypasses VizieR to avoid XML parsing errors.
Usage: python fetch_cg22_cluster.py <cluster_name>
Example: python fetch_cg22_cluster.py "Pleiades"
License: CC0 1.0 Universal
"""
import os
import sys
import argparse
import pandas as pd
from astroquery.gaia import Gaia

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str, help="Cluster name (e.g., Pleiades, Hyades, Praesepe)")
    args = parser.parse_args()
    
    cluster_name = args.name.lower()
    output_file = os.path.join(REF_DIR, f"{cluster_name}_cg22_dr3.csv")
    
    print(f"🔭 Fetching {args.name} from CG22 via Gaia Archive...")
    
    # ADQL Query for CG22 members
    # Note: We use the official table name in the Gaia Archive
    query = f"""
    SELECT g.source_id, g.ra, g.dec, g.parallax, g.pmra, g.pmdec,
           g.phot_g_mean_mag, g.ruwe, g.parallax_error, g.pmra_error, g.pmdec_error,
           c.Pmem
    FROM gaiadr3.gaia_source AS g
    JOIN external.gaia_dr3_cantat_gaudin_2022 AS c
    ON g.source_id = c.source_id
    WHERE LOWER(c.name) = '{cluster_name}'
      AND c.Pmem >= 0.9
    """
    
    try:
        job = Gaia.launch_job(query)
        df = job.get_results().to_pandas()
    except Exception as e:
        print(f"❌ Query failed: {e}")
        print("   Note: Ensure 'external.gaia_dr3_cantat_gaudin_2022' is available in the archive.")
        return

    if len(df) == 0:
        print(f"⚠️  No members found for '{cluster_name}'. Check spelling or catalog availability.")
        return

    # Rename to TRACEBIND schema
    rename_map = {"Pmem": "member_prob"}
    df = df.rename(columns=rename_map)
    
    # Quality Cuts
    n_before = len(df)
    df = df[df["parallax"] > 0].copy()
    df = df[df["ruwe"] < 1.4].copy()
    df = df[df["phot_g_mean_mag"] < 18.0].copy()
    
    # Parallax S/N > 10
    if "parallax_error" in df.columns:
        df = df[df["parallax_error"] > 0].copy()
        df["plx_sn"] = df["parallax"] / df["parallax_error"]
        df = df[df["plx_sn"] > 10].copy()
        
    df = df.dropna(subset=["parallax", "pmra", "pmdec"])
    df = df.reset_index(drop=True)
    
    print(f"   Filtered: {n_before} → {len(df)} members")
    
    # Sanity Check
    if len(df) > 0:
        med_dist = (1000.0 / df["parallax"]).median()
        print(f"   Median distance: {med_dist:.1f} pc")
        
    os.makedirs(REF_DIR, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"✅ Saved {cluster_name} to {output_file}")

if __name__ == "__main__":
    main()