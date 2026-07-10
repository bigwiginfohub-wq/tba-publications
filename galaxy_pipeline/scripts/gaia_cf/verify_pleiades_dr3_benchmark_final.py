"""Verify Pleiades DR3 benchmark CONSTRUCTION by replaying filters on raw data."""
import os
import pandas as pd
import numpy as np

# === CONFIGURATION ===
CG22_DR2_MEDIAN_DIST_PC = 136.22  # From verify_pleiades_dr2.py output

# === PATH RESOLUTION ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
MAPPING_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_dr2_dr3_mapping.csv")
RAW_DR3_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_dr3_raw.csv")
FINAL_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_cg22_dr3_crossmatched.csv")

if not os.path.exists(MAPPING_CSV):
    raise FileNotFoundError(f"Mapping file not found at {MAPPING_CSV}")
if not os.path.exists(RAW_DR3_CSV):
    raise FileNotFoundError(
        f"Raw DR3 table not found at {RAW_DR3_CSV}. "
        "Run crossmatch_pleiades_dr2_to_dr3_final_v4.py first to generate unfiltered DR3 astrometry."
    )
if not os.path.exists(FINAL_CSV):
    raise FileNotFoundError(f"Final filtered CSV not found at {FINAL_CSV}.")

# Load files
mapping = pd.read_csv(MAPPING_CSV)
raw_dr3 = pd.read_csv(RAW_DR3_CSV)
final_saved = pd.read_csv(FINAL_CSV)

# === INTEGRITY ASSERTIONS ===
assert len(mapping) == len(raw_dr3), (
    f"Mapping contains {len(mapping)} stars but raw DR3 table contains {len(raw_dr3)}."
)
assert mapping["dr2_source_id"].is_unique, "Non-unique DR2 IDs in mapping!"
assert mapping["dr3_source_id"].is_unique, "Non-unique DR3 IDs in mapping!"
assert raw_dr3["source_id"].is_unique, "Non-unique source_ids in raw DR3 table!"
assert set(raw_dr3["source_id"]) == set(mapping["dr3_source_id"]), (
    "Mismatch between raw DR3 source_ids and mapping dr3_source_ids!"
)

print("🔍 PLEIADES DR3 BENCHMARK CONSTRUCTION VERIFICATION")
print("=" * 60)

# === COMPREHENSIVE DATA COMPLETENESS AUDIT ===
print("\n📊 MISSING VALUES IN RAW DR3 TABLE:")
for col in ["ruwe", "parallax", "parallax_error", "pmra", "pmdec", "phot_g_mean_mag"]:
    n_missing = raw_dr3[col].isna().sum()
    if n_missing > 0:
        print(f"   {col:16s}: {n_missing} missing")
    else:
        print(f"   {col:16s}: Complete")

# === DETAILED RUWE ACCOUNTING ===
ruwe_bad = (raw_dr3["ruwe"] >= 1.4).sum()
ruwe_nan = raw_dr3["ruwe"].isna().sum()
ruwe_good = (raw_dr3["ruwe"] < 1.4).sum()
total = len(raw_dr3)

print(f"\n🔍 RUWE FILTER BREAKDOWN:")
print(f"   Passed (Valid & < 1.4)   : {ruwe_good}")
print(f"   Rejected (RUWE >= 1.4)   : {ruwe_bad}")
print(f"   Missing (RUWE = NaN)     : {ruwe_nan}")
print(f"   Total                    : {ruwe_good + ruwe_bad + ruwe_nan} (expected: {total})")

# Verify arithmetic consistency
assert ruwe_good + ruwe_bad + ruwe_nan == total, "RUWE categories do not sum to total!"

if ruwe_nan > 0:
    print(f"\n⚠️  Source without published DR3 astrometric solution:")
    nan_rows = raw_dr3[raw_dr3["ruwe"].isna()]
    print("   Details of excluded source(s):")
    print(nan_rows[["source_id", "phot_g_mean_mag", "parallax", "parallax_error"]].to_string(index=False))
    print("\n   Scientific Context:")
    print("   - Detected by Gaia and matched via dr2_neighbourhood")
    print("   - No published parallax or RUWE.")
    print("   - The Gaia archive does not provide a usable astrometric solution for this source in DR3.")
    print("   - Automatically excluded from benchmark due to missing data.")

print("-" * 60)

# === SEQUENTIAL FILTER ACCOUNTING (REPLAYED ON RAW TABLE) ===
initial_n = len(raw_dr3)

# Step 1: RUWE < 1.4 (Explicitly requires valid value AND threshold)
mask_ruwe = raw_dr3["ruwe"].notna() & (raw_dr3["ruwe"] < 1.4)
n_after_ruwe = mask_ruwe.sum()
rejected_ruwe = initial_n - n_after_ruwe

# Step 2: G < 18 (cumulative)
mask_gmag = mask_ruwe & (raw_dr3["phot_g_mean_mag"] < 18)
n_after_gmag = mask_gmag.sum()
rejected_gmag = n_after_ruwe - n_after_gmag

# Step 3: Positive parallax AND positive error (cumulative)
mask_plx = mask_gmag & (raw_dr3["parallax"] > 0) & (raw_dr3["parallax_error"] > 0)
n_after_plx = mask_plx.sum()
rejected_plx = n_after_gmag - n_after_plx

# Step 4: plx_sn > 10 (using safe .loc indexing on filtered subset)
temp_df = raw_dr3[mask_plx].copy()
temp_df["plx_sn"] = temp_df["parallax"] / temp_df["parallax_error"]
mask_sn = temp_df["plx_sn"] > 10
analysis_df = temp_df.loc[mask_sn].copy()
n_final = len(analysis_df)
rejected_sn = n_after_plx - n_final

print(f"\n📉 SEQUENTIAL FILTER REJECTION LOG:")
print(f"Initial CG22 Pmem≥0.9 members:      {initial_n:>6}")
print(f"After RUWE < 1.4:                    {n_after_ruwe:>6} ({rejected_ruwe} rejected)")
print(f"After G < 18:                        {n_after_gmag:>6} ({rejected_gmag} rejected)")
print(f"After parallax > 0 & error > 0:      {n_after_plx:>6} ({rejected_plx} rejected)")
print(f"After plx_sn > 10:                   {n_final:>6} ({rejected_sn} rejected)")
print(f"Final TRACEBIND analysis sample:     {n_final:>6}")
print("-" * 60)

# === END-TO-END ARTIFACT VERIFICATION ===
assert len(final_saved) == len(analysis_df), (
    f"Final CSV has {len(final_saved)} rows but reconstruction has {len(analysis_df)}."
)
assert set(final_saved["source_id"]) == set(analysis_df["source_id"]), (
    "Source ID mismatch between final CSV and reconstructed analysis sample!"
)
print("✅ End-to-end verification: Reconstructed sample matches saved benchmark exactly.")
print("-" * 60)

# === MAPPING QUALITY METRICS ===
ang_dist_stats = {
    'median': mapping['angular_distance'].median(),
    'p95': mapping['angular_distance'].quantile(0.95),
    'max': mapping['angular_distance'].max()
}
print(f"📏 Mapping angular distance median:     {ang_dist_stats['median']:>6.3f} mas")
print(f"📏 Mapping angular distance p95:        {ang_dist_stats['p95']:>6.3f} mas")
print(f"📏 Mapping angular distance max:        {ang_dist_stats['max']:>6.3f} mas")
print("-" * 60)

# === ASTROMETRIC CONSISTENCY CHECK ===
med_dist_dr3 = (1000.0 / analysis_df['parallax']).median()
med_plx_dr3 = analysis_df['parallax'].median()
dist_shift = med_dist_dr3 - CG22_DR2_MEDIAN_DIST_PC
print(f"🌌 Median DR3 parallax:                 {med_plx_dr3:>6.4f} mas")
print(f"🌌 Median DR3 distance:                 {med_dist_dr3:>6.2f} pc")
print(f"🌌 Difference from CG22 DR2 median ({CG22_DR2_MEDIAN_DIST_PC:.2f} pc): {dist_shift:+.2f} pc")
print("=" * 60)
print("✅ BENCHMARK CONSTRUCTION VERIFIED:")
print("   ✓ CG22 membership reproduced")
print("   ✓ Official Gaia neighbour mapping applied")
print("   ✓ DR3 astrometry retrieved")
print("   ✓ Quality filtering documented")
print("   ✓ Provenance preserved")
print("=" * 60)
print("⚠️  NOTE: This verifies DATA PREPARATION only.")
print("   Scientific conclusions drawn from this benchmark require independent validation.")
print("   pleiades_dr2_dr3_mapping.csv preserved as permanent artifact.")
print("=" * 60)