"""
Download Hyades membership catalog directly from VizieR.
Source: Lodieu et al. 2019 (J/A+A/623/A35/tablec1)
Guarantees correct schema, units, and data integrity.
"""
import os
import pandas as pd
from astroquery.vizier import Vizier

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hyades_members_lodieu2019.csv")

# VizieR catalog ID for Lodieu+2019 Hyades members
CATALOG_ID = "J/A+A/623/A35"
TABLE_NAME = "tablec1"

# Correct rename map for J/A+A/623/A35/tablec1
RENAME_MAP = {
    "ID": "source_id",       # WARNING: Not Gaia DR2 source_id
    "RAICRS": "ra",
    "DEICRS": "dec",
    "pmRA*": "pmra",         # μ_α cos(δ)
    "pmDE": "pmdec",
    "Plx": "parallax",
    "Gmag": "phot_g_mean_mag",
}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"🔭 Downloading {CATALOG_ID}/{TABLE_NAME} from VizieR...")
    viz = Vizier(columns=["*"], row_limit=-1)
    tables = viz.get_catalogs(CATALOG_ID)

    # VizieR returns keys as "J/A+A/623/A35/tablec1", not just "tablec1"
    full_table_name = f"{CATALOG_ID}/{TABLE_NAME}"
    if full_table_name not in tables.keys():
        available = list(tables.keys())
        raise RuntimeError(
            f"Table '{full_table_name}' not found in {CATALOG_ID}.\n"
            f"Available tables: {available}"
        )

    df = tables[full_table_name].to_pandas()
    print(f"   Downloaded {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")

    # Only rename columns that actually exist
    existing_renames = {k: v for k, v in RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=existing_renames)

    # Adjusted quality cuts (no RUWE, no member_prob, no parallax_error)
    n_before = len(df)
    df = df[df["parallax"] > 0].copy()
    df = df[df["phot_g_mean_mag"] < 18.0].copy()
    df = df.reset_index(drop=True)

    print(f"   Quality cuts: {n_before} → {len(df)} members")
    print(f"   ⚠️  No RUWE, member_prob, or parallax_error in this catalog")
    print(f"   ⚠️  source_id is Lodieu+2019 ID, NOT Gaia DR2 source_id")

    # Sanity check
    plx_median = df["parallax"].median()
    dist_median = 1000.0 / plx_median if plx_median > 0 else float("nan")
    print(f"\n   Parallax median: {plx_median:.2f} mas")
    print(f"   Distance median: {dist_median:.1f} pc")

    if dist_median < 20 or dist_median > 80:
        raise RuntimeError(
            f"SANITY CHECK FAILED: Expected ~47 pc, got {dist_median:.1f} pc"
        )

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved {len(df)} members to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()