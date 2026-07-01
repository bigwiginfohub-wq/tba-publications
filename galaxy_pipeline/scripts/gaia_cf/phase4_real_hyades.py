"""
TRACEBIND Phase 4 V5: Real Gaia DR3 Hyades Application (Locked)
Uses shared tracebind.metric module. Saves run metadata.
No dead code. No unused Galactic constants.
License: CC0 1.0 Universal
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, mannwhitneyu
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up TWO levels: gaia_cf -> scripts -> GaiaProject
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, _SCRIPT_DIR)

from tracebind.metric import (
    astrometry_to_cartesian,
    compute_ratio_distribution,
    TRACEBIND_METRIC_VERSION,
)

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "real")
HYADES_FILE = os.path.join(_PROJECT_ROOT, "data", "reference", "hyades_gaia_dr3.csv")
FIELD_CACHE = os.path.join(OUTPUT_DIR, "hyades_field_control_v5.csv")
METADATA_FILE = os.path.join(OUTPUT_DIR, "phase4_v5_metadata.json")

K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 200
RANDOM_SEED = 42
SEPARATION_Q_SIG = 97.5
SEPARATION_Q_CTRL = 2.5
MIN_FIELD_SIZE = 60


def load_hyades_members(path):
    """Load and validate Hyades reference catalog."""
    if not os.path.exists(path):
        raise RuntimeError(f"Hyades catalog not found: {path}")
    
    df = pd.read_csv(path)
    required = {"source_id", "ra", "dec", "parallax", "pmra", "pmdec", "phot_g_mean_mag"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Catalog missing columns: {missing}")

    # Quality cuts
    n_before = len(df)
    df = df[(df["parallax"] > 0) & (df["phot_g_mean_mag"] < 18.0)].copy()
    if "member_prob" in df.columns:
        df = df[df["member_prob"] > 0.7].copy()
    df = df.reset_index(drop=True)

    print(f"📂 Loaded {len(df)}/{n_before} Hyades members from {os.path.basename(path)}")
    return df


def generate_matched_field(hyades_df, seed=42):
    """Generate magnitude-matched field control via RA/Dec box + parallax exclusion."""
    if os.path.exists(FIELD_CACHE):
        print(f"📂 Loading cached field from {FIELD_CACHE}")
        field_df = pd.read_csv(FIELD_CACHE)
        if len(field_df) < MIN_FIELD_SIZE:
            raise RuntimeError(f"Cached field too small ({len(field_df)}). Delete and regenerate.")
        ks_stat, ks_pval = ks_2samp(
            hyades_df["phot_g_mean_mag"], field_df["phot_g_mean_mag"]
        )
        return field_df, ks_stat, ks_pval

    rng = np.random.default_rng(seed)
    n_target = len(hyades_df)

    # RA/Dec bounding box with buffer
    ra_min = hyades_df["ra"].min() - 5.0
    ra_max = hyades_df["ra"].max() + 5.0
    dec_min = hyades_df["dec"].min() - 5.0
    dec_max = hyades_df["dec"].max() + 5.0

    print(f"🔭 Querying field in RA[{ra_min:.2f},{ra_max:.2f}] Dec[{dec_min:.2f},{dec_max:.2f}]...")
    from astroquery.gaia import Gaia
    query = f"""
    SELECT TOP {n_target * 20} g.source_id, g.ra, g.dec, g.parallax, g.pmra, g.pmdec,
           g.phot_g_mean_mag, g.ruwe
    FROM gaiadr3.gaia_source AS g
    WHERE g.ra BETWEEN {ra_min} AND {ra_max}
      AND g.dec BETWEEN {dec_min} AND {dec_max}
      AND g.phot_g_mean_mag < 19.0
      AND g.parallax > 0.1
      AND g.parallax < 15.0
    """
    job = Gaia.launch_job(query)
    candidates = job.get_results().to_pandas()
    print(f"   Raw candidates: {len(candidates)}")

    # Parallax exclusion zone
    plx_lo = hyades_df["parallax"].quantile(0.01)
    plx_hi = hyades_df["parallax"].quantile(0.99)
    candidates = candidates[
        (candidates["parallax"] < plx_lo) | (candidates["parallax"] > plx_hi)
    ].reset_index(drop=True)
    print(f"   After parallax exclusion: {len(candidates)}")

    if len(candidates) < MIN_FIELD_SIZE:
        raise RuntimeError(f"Only {len(candidates)} field candidates. Need ≥{MIN_FIELD_SIZE}.")

    # Deterministic NN magnitude matching (unique only)
    hyd_g = hyades_df["phot_g_mean_mag"].values
    fld_g = candidates["phot_g_mean_mag"].values
    nn = NearestNeighbors(n_neighbors=min(10, len(candidates)), metric='euclidean')
    nn.fit(fld_g.reshape(-1, 1))
    distances, indices = nn.kneighbors(hyd_g.reshape(-1, 1))

    used = set()
    matched = []
    order = np.argsort(distances.flatten())
    for idx in order:
        fi = indices[idx // indices.shape[1], idx % indices.shape[1]]
        if fi not in used:
            used.add(fi)
            matched.append(fi)
        if len(matched) >= min(n_target, len(candidates)):
            break

    if len(matched) < MIN_FIELD_SIZE:
        raise RuntimeError(f"Magnitude matching yielded only {len(matched)} unique stars.")

    field_df = candidates.iloc[matched[:n_target]].reset_index(drop=True)
    ks_stat, ks_pval = ks_2samp(hyd_g, field_df["phot_g_mean_mag"].values)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    field_df.to_csv(FIELD_CACHE, index=False)
    print(f"   Matched field: {len(field_df)} | KS={ks_stat:.4f} (p={ks_pval:.4f})")
    print(f"💾 Cached to {FIELD_CACHE}")
    return field_df, ks_stat, ks_pval


def main():
    print("🔬 TRACEBIND PHASE 4 V5: REAL GAIA DR3 HYADES (LOCKED)")
    print("=" * 90)

    hyades = load_hyades_members(HYADES_FILE)
    field, ks_stat, ks_pval = generate_matched_field(hyades, seed=RANDOM_SEED)

    # Astrometric diagnostics for both populations
    plx_snr = (hyades["parallax"] / hyades["parallax_error"]).median() \
        if "parallax_error" in hyades.columns else np.nan
    med_dist = (1000.0 / hyades["parallax"]).median()

    print(f"\n✅ Sample sizes: Hyades={len(hyades)}, Field={len(field)}")
    print(f"   Hyades median RUWE: {hyades['ruwe'].median():.2f}" if "ruwe" in hyades.columns else "")
    print(f"   Hyades median plx S/N: {plx_snr:.1f}" if not np.isnan(plx_snr) else "")
    print(f"   Hyades median distance: {med_dist:.1f} pc")
    print(f"   Field median parallax: {field['parallax'].median():.2f} mas")
    print(f"   Field PM dispersion: {np.sqrt(field['pmra']**2 + field['pmdec']**2).std():.2f} mas/yr")
    print(f"   G-mag KS: {ks_stat:.4f} (p={ks_pval:.4f})")

    # INDEPENDENT RNG streams
    master_rng = np.random.default_rng(RANDOM_SEED)
    rng_hyd = np.random.default_rng(master_rng.integers(0, 2**31))
    rng_fld = np.random.default_rng(master_rng.integers(0, 2**31))

    print(f"\n⚙️  Running V11 metric (k={K_PREDICT}, perms={N_PERMUTATIONS})...")
    pos_hyd = astrometry_to_cartesian(hyades["ra"].values, hyades["dec"].values, hyades["parallax"].values)
    hyd_dist = compute_ratio_distribution(
        pos_hyd, hyades["pmra"].values, hyades["pmdec"].values,
        K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_hyd
    )

    pos_fld = astrometry_to_cartesian(field["ra"].values, field["dec"].values, field["parallax"].values)
    fld_dist = compute_ratio_distribution(
        pos_fld, field["pmra"].values, field["pmdec"].values,
        K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, rng_fld
    )

    hyd_med = np.median(hyd_dist) if len(hyd_dist) > 0 else np.nan
    fld_med = np.median(fld_dist) if len(fld_dist) > 0 else np.nan
    sig_q = np.percentile(hyd_dist, SEPARATION_Q_SIG) if len(hyd_dist) > 10 else np.nan
    ctrl_q = np.percentile(fld_dist, SEPARATION_Q_CTRL) if len(fld_dist) > 10 else np.nan
    separated = sig_q < ctrl_q if not (np.isnan(sig_q) or np.isnan(ctrl_q)) else False

    mw_stat, mw_p = mannwhitneyu(hyd_dist, fld_dist, alternative='less') \
        if (len(hyd_dist) > 0 and len(fld_dist) > 0) else (np.nan, np.nan)
    effect_size = mw_stat / (len(hyd_dist) * len(fld_dist)) if not np.isnan(mw_stat) else np.nan

    print("\n" + "=" * 90)
    print("📊 RESULTS")
    print("-" * 50)
    print(f"  Hyades median ratio:     {hyd_med:.4f}")
    print(f"  Field median ratio:      {fld_med:.4f}")
    print(f"  Hyades Q_{SEPARATION_Q_SIG:.1f}:          {sig_q:.4f}")
    print(f"  Field  Q_{SEPARATION_Q_CTRL:.1f}:          {ctrl_q:.4f}")
    print(f"  Mann-Whitney p:          {mw_p:.2e}")
    print(f"  Effect size:             {effect_size:.3f}")
    print(f"\n  Formal separation criterion:")
    print(f"    Q_{SEPARATION_Q_SIG:.1f}(R_hyades) < Q_{SEPARATION_Q_CTRL:.1f}(R_field)")
    print(f"    {sig_q:.4f} {'<' if separated else '≥'} {ctrl_q:.4f}")
    print(f"  Result: {'✅ SEPARATED' if separated else '❌ NOT SEPARATED'}")

    # Save outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ratio_file = os.path.join(OUTPUT_DIR, "phase4_v5_ratio_distributions.csv")
    pd.DataFrame({
        "population": ["hyades"] * len(hyd_dist) + ["field"] * len(fld_dist),
        "ratio": np.concatenate([hyd_dist, fld_dist])
    }).to_csv(ratio_file, index=False)

    id_file = os.path.join(OUTPUT_DIR, "phase4_v5_source_ids.csv")
    pd.DataFrame({
        "population": ["hyades"] * len(hyades) + ["field"] * len(field),
        "source_id": list(hyades["source_id"]) + list(field["source_id"])
    }).to_csv(id_file, index=False)

    # Save run metadata
    metadata = {
        "metric_version": TRACEBIND_METRIC_VERSION,
        "k_predict": K_PREDICT,
        "k_shuffle": K_SHUFFLE,
        "n_permutations": N_PERMUTATIONS,
        "random_seed": RANDOM_SEED,
        "separation_criterion": f"Q{SEPARATION_Q_SIG}(sig) < Q{SEPARATION_Q_CTRL}(ctrl)",
        "hyades_catalog": os.path.basename(HYADES_FILE),
        "field_cache": os.path.basename(FIELD_CACHE),
        "n_hyades": len(hyades),
        "n_field": len(field),
        "hyades_median_ratio": hyd_med,
        "field_median_ratio": fld_med,
        "separated": separated,
        "mann_whitney_p": mw_p,
        "effect_size": effect_size,
        "g_mag_ks_stat": ks_stat,
        "g_mag_ks_pval": ks_pval,
    }
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"\n💾 Ratios saved to {ratio_file}")
    print(f"💾 Source IDs saved to {id_file}")
    print(f"💾 Metadata saved to {METADATA_FILE}")
    print("\n🔒 PHASE 4 V5 CHECKPOINT:")
    print("- Metric: Imported from tracebind.metric (single source of truth)")
    print("- Implementation: Publication-grade under inverse-parallax approximation")
    print("- Field: RA/Dec box + parallax exclusion + deterministic NN mag matching")
    print("- Metadata: All parameters saved as JSON for full reproducibility")
    print("- Status: LOCKED FOR PUBLICATION")


if __name__ == "__main__":
    main()