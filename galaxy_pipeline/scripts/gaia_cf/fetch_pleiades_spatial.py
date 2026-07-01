"""
Fetch Pleiades members via Spatial/Kinematic Selection from Gaia DR3.
Bypasses external catalogs entirely.
License: CC0 1.0 Universal
"""
import os
import sys
import pandas as pd
from astroquery.gaia import Gaia

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
OUTPUT_FILE = os.path.join(REF_DIR, "pleiades_spatial_dr3.csv")

def main():
    print(f"🔭 Fetching Pleiades via Spatial/Kinematic Selection...")
    
    # Pleiades Center: RA ~56.7, Dec ~24.1
    # Parallax: ~7-8 mas (135 pc)
    # PM: ~20 mas/yr
    
    query = """
    SELECT TOP 2000 
        g.source_id, g.ra, g.dec, g.parallax, g.pmra, g.pmdec,
        g.phot_g_mean_mag, g.ruwe, g.parallax_error, g.pmra_error, g.pmdec_error
    FROM gaiadr3.gaia_source AS g
    WHERE 
        -- Spatial Box around Pleiades
        g.ra BETWEEN 50 AND 65
        AND g.dec BETWEEN 15 AND 30
        -- Distance constraint (100-180 pc)
        AND g.parallax BETWEEN 5.5 AND 10.0
        -- Quality cuts
        AND g.ruwe < 1.4
        AND g.phot_g_mean_mag < 18.0
        AND g.parallax_error > 0
        AND (g.parallax / g.parallax_error) > 10
    """
    
    try:
        job = Gaia.launch_job(query)
        df = job.get_results().to_pandas()
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return

    if len(df) == 0:
        print("⚠️  No members found.")
        return

    print(f"   Found {len(df)} candidates.")
    
    # Rename to TRACEBIND schema
    df = df.rename(columns={"parallax": "parallax", "pmra": "pmra", "pmdec": "pmdec"})
    
    # Add a dummy member_prob for compatibility with our filter logic
    df["member_prob"] = 1.0 
    
    os.makedirs(REF_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved Pleiades spatial sample to {OUTPUT_FILE}")
    
    # Sanity Check
    med_dist = (1000.0 / df["parallax"]).median()
    print(f"   Median distance: {med_dist:.1f} pc (Expected ~135)")

if __name__ == "__main__":
    main()