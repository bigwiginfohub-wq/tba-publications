"""
TRACEBIND v2.0 - Projection Control Generator Audit (CORRECTED)
Uses cosine similarity (not Pearson on 2-pt vectors) to measure
intrinsic local velocity alignment. Independent of prediction metric.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))\n_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))\nINPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")

K_AUDIT = 20


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def compute_local_velocity_alignment(positions_3d, pmra, pmdec, k):
    """
    For each star: compute COSINE SIMILARITY between its PM vector
    and the mean PM vector of its k nearest neighbors.
    
    Returns median cosine similarity across population.
    +1 = aligned, 0 = orthogonal, -1 = anti-aligned.
    """
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2:
        return np.nan

    pm_vectors = np.column_stack([pmra, pmdec])
    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]

    neighbor_mean_pm = np.mean(pm_vectors[indices], axis=1)  # (n, 2)

    # Vectorized cosine similarity
    dots = np.sum(pm_vectors * neighbor_mean_pm, axis=1)
    norms_own = np.linalg.norm(pm_vectors, axis=1)
    norms_nbr = np.linalg.norm(neighbor_mean_pm, axis=1)
    denom = norms_own * norms_nbr

    # Guard against zero-norm vectors
    valid = denom > 1e-10
    cosines = np.full(n, np.nan)
    cosines[valid] = dots[valid] / denom[valid]

    return float(np.nanmedian(cosines))


def main():
    print("🔬 PROJECTION CONTROL GENERATOR AUDIT (CORRECTED)")
    print("=" * 60)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows | k_audit={K_AUDIT}\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())

    print(f"📊 Intrinsic Local Velocity Alignment (Cosine Similarity):")
    print("-" * 60)
    print(f"  {'Population':<20s} {'Med Cosine':>12s} {'Interpretation':>20s}")
    print("-" * 60)

    results = {}
    for pop in populations:
        mask = df["population"] == pop
        cos = compute_local_velocity_alignment(
            positions_3d[mask],
            df.loc[mask, "pmra"].values,
            df.loc[mask, "pmdec"].values,
            K_AUDIT
        )
        results[pop] = cos

        if np.isnan(cos):
            print(f"  {pop:<20s} {'NaN':>12s} {'ERROR':>20s}")
            continue

        if cos > 0.7:
            interp = "⚠️ STRONG ALIGNMENT"
        elif cos > 0.3:
            interp = "⚠️ MODERATE ALIGNMENT"
        elif cos > 0.1:
            interp = "⚡ WEAK ALIGNMENT"
        else:
            interp = "✅ NULL (no alignment)"

        print(f"  {pop:<20s} {cos:>12.4f} {interp:>20s}")

    # === SYNTHESIS ===
    print("\n" + "=" * 60)
    print("🧪 AUDIT SYNTHESIS")
    print("-" * 40)

    sig_cos = results.get("signal", np.nan)
    prj_cos = results.get("projection_control", np.nan)
    fld_cos = results.get("field_control", np.nan)

    print(f"  Signal alignment:     {sig_cos:.4f}" if not np.isnan(sig_cos) else "  Signal: NaN")
    print(f"  Projection alignment: {prj_cos:.4f}" if not np.isnan(prj_cos) else "  Projection: NaN")
    print(f"  Field alignment:      {fld_cos:.4f}" if not np.isnan(fld_cos) else "  Field: NaN")

    if not np.isnan(prj_cos) and not np.isnan(fld_cos):
        gap = prj_cos - fld_cos
        print(f"\n  Projection − Field gap: {gap:+.4f}")

        if prj_cos > 0.3 and gap > 0.15:
            print("\n  🎯 VERDICT: Projection control contains INTRINSIC alignment.")
            print("     V11 ratio=0.761 is likely detecting REAL structure in the")
            print("     synthetic population, NOT metric bias.")
            print("     ACTION: Redesign projection generator, NOT the metric.")
        elif prj_cos <= 0.1 and abs(gap) < 0.05:
            print("\n  🎯 VERDICT: Projection control is genuinely null.")
            print("     V11 ratio=0.761 indicates RESIDUAL METRIC BIAS.")
            print("     ACTION: Further metric refinement needed.")
        else:
            print("\n  🎯 VERDICT: AMBIGUOUS — alignment is weak but non-zero.")
            print("     May require tighter generator audit or accept marginal pass.")

    print("\n🔒 AUDIT CHECKPOINT (CORRECTED):")
    print("- Metric: Cosine similarity (NOT Pearson on 2-pt vectors)")
    print("- Measures genuine directional alignment in velocity space")
    print(f"- k_audit: {K_AUDIT}")
    print(f"- Input: {INPUT_FILE}")


if __name__ == "__main__":
    main()
