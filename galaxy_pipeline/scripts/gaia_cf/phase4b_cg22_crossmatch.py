"""
Phase 4B: High-Purity Hyades Membership via Lodieu+2019 ∩ CG22 Consensus
Intentionally conservative: reduces contamination below Phase 3A boundary.
Replaces Lodieu astrometry with Gaia DR3 values from CG22.
License: CC0 1.0 Universal
"""
import os
import numpy as np
import pandas as pd
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
REF_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
REAL_DIR = os.path.join(_PROJECT_ROOT, "data", "real")

LODIEU_FILE = os.path.join(REF_DIR, "hyades_members_lodieu2019.csv")
OUTPUT_FILE = os.path.join(REAL_DIR, "hyades_consensus_pmem90_members.csv")

PMEM_THRESHOLD = 0.9
MATCH_RADIUS_ARCSEC = 2.0
# Hyades center from Cantat-Gaudin+2022 (J/A+A/658/A41)
HYADES_CENTER_RA = 67.0
HYADES_CENTER_DEC = 16.0
HYADES_RADIUS_DEG = 10.0  # Angular selection radius


def load_lodieu_members():
    """Load Lodieu+2019 reference with column validation."""
    if not os.path.exists(LODIEU_FILE):
        raise RuntimeError(f"Lodieu reference not found: {LODIEU_FILE}")

    df = pd.read_csv(LODIEU_FILE)
    required = ["ra", "dec"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"Lodieu CSV missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )
    print(f"📂 Loaded {len(df)} Lodieu+2019 members")
    return df


def fetch_cg22_hyades():
    """Fetch CG22 Hyades members with safe table key handling."""
    print(f"🔭 Querying CG22 (J/A+A/658/A41) for Pmem >= {PMEM_THRESHOLD}...")
    viz = Vizier(
        columns=["source_id", "RA_ICRS", "DE_ICRS", "Plx", "pmRA", "pmDE",
                 "Gmag", "RUWE", "e_Plx", "e_pmRA", "e_pmDE", "Pmem"],
        row_limit=-1
    )
    # SAFE: Query parent catalog, then extract table by key
    tables = viz.get_catalogs("J/A+A/658/A41")
    table_key = "J/A+A/658/A41/table2"
    if table_key not in tables.keys():
        raise RuntimeError(
            f"Table '{table_key}' not found. Available: {list(tables.keys())}"
        )

    df = tables[table_key].to_pandas()

    # Filter to Hyades via angular separation (not rectangular RA/Dec box)
    coords = SkyCoord(ra=df["RA_ICRS"].values * u.deg,
                      dec=df["DE_ICRS"].values * u.deg)
    center = SkyCoord(ra=HYADES_CENTER_RA * u.deg, dec=HYADES_CENTER_DEC * u.deg)
    sep = coords.separation(center).deg
    df = df[sep <= HYADES_RADIUS_DEG].copy()

    # Apply membership probability cut
    df = df[df["Pmem"] >= PMEM_THRESHOLD].copy()
    print(f"   Retrieved {len(df)} CG22 sources within {HYADES_RADIUS_DEG}° of Hyades center")
    return df


def crossmatch_and_merge(lodieu_df, cg22_df):
    """One-to-one positional cross-match with duplicate removal."""
    print(f"🔗 Cross-matching (radius={MATCH_RADIUS_ARCSEC}\")...")
    lodieu_coords = SkyCoord(ra=lodieu_df["ra"].values * u.deg,
                             dec=lodieu_df["dec"].values * u.deg)
    cg22_coords = SkyCoord(ra=cg22_df["RA_ICRS"].values * u.deg,
                           dec=cg22_df["DE_ICRS"].values * u.deg)

    idx, sep, _ = lodieu_coords.match_to_catalog_sky(cg22_coords)
    match_mask = sep.arcsec <= MATCH_RADIUS_ARCSEC

    matched_lodieu = lodieu_df.iloc[np.where(match_mask)[0]].copy()
    matched_cg22 = cg22_df.iloc[idx[match_mask]].copy()

    # Reset indices for safe concatenation (avoids index-based merge fragility)
    matched_lodieu = matched_lodieu.reset_index(drop=True)
    matched_cg22 = matched_cg22.reset_index(drop=True)

    # Concatenate side-by-side
    merged = pd.concat([matched_lodieu, matched_cg22], axis=1)

    # Remove duplicate Gaia DR3 source_ids (many-to-one protection)
    n_before = len(merged)
    merged = merged.drop_duplicates(subset="source_id")
    n_after = len(merged)
    if n_before != n_after:
        print(f"   ⚠️  Removed {n_before - n_after} duplicate CG22 matches")

    print(f"   Matched: {n_after} consensus members")
    return merged


def build_output(merged):
    """Extract CG22 DR3 astrometry, validate, and return clean output."""
    output = merged[[
        "source_id", "RA_ICRS", "DE_ICRS", "Plx", "pmRA", "pmDE",
        "Gmag", "RUWE", "e_Plx", "e_pmRA", "e_pmDE", "Pmem"
    ]].rename(columns={
        "RA_ICRS": "ra", "DE_ICRS": "dec", "Plx": "parallax",
        "pmRA": "pmra", "pmDE": "pmdec", "Gmag": "phot_g_mean_mag",
        "e_Plx": "parallax_error", "e_pmRA": "pmra_error",
        "e_pmDE": "pmdec_error"
    })

    # Publication-grade validation: fail loudly on unexpected results
    if len(output) < 100:
        raise RuntimeError(
            f"Only {len(output)} consensus members. Expected >100. "
            "Check match radius or Pmem threshold."
        )

    med_plx = output["parallax"].median()
    if med_plx < 15:
        raise RuntimeError(
            f"Median parallax {med_plx:.2f} mas inconsistent with Hyades (~21 mas). "
            "Possible catalog misalignment."
        )

    med_ruwe = output["ruwe"].median()
    if med_ruwe > 1.4:
        raise RuntimeError(
            f"Median RUWE {med_ruwe:.3f} exceeds 1.4. Astrometric quality unexpectedly poor."
        )

    return output


def main():
    os.makedirs(REAL_DIR, exist_ok=True)

    lodieu = load_lodieu_members()
    cg22 = fetch_cg22_hyades()
    merged = crossmatch_and_merge(lodieu, cg22)
    output = build_output(merged)

    output.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ Saved {len(output)} consensus members to {OUTPUT_FILE}")
    print(f"   Median parallax: {output['parallax'].median():.2f} mas")
    print(f"   Median distance: {(1000.0 / output['parallax']).median():.1f} pc")
    print(f"   Median RUWE: {output['ruwe'].median():.3f}")
    print(f"   Pmem range: [{output['Pmem'].min():.4f}, {output['Pmem'].max():.4f}]")
    print(f"\n🔒 PHASE 4B CHECKPOINT:")
    print(f"- Strategy: Conservative consensus (Lodieu ∩ CG22 Pmem≥{PMEM_THRESHOLD})")
    print(f"- Astrometry: Gaia DR3 (CG22), NOT Lodieu DR2")
    print(f"- Selection: Angular radius {HYADES_RADIUS_DEG}° from Hyades center")
    print(f"- Matching: One-to-one, duplicates removed")
    print(f"- Validation: Count, parallax, RUWE checks enforced")
    print(f"- Status: HIGH-PURITY CONSENSUS CATALOG READY")


if __name__ == "__main__":
    main()