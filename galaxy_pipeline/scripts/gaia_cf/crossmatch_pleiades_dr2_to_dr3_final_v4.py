"""
Cross-match Pleiades DR2 members to Gaia DR3 via official neighbour table.
Anonymous execution; no authentication required.
Duplicate resolution: smallest angular_distance (documented methodological choice).
Preserves full neighbour diagnostics and unmatched source accounting.
"""
import os
from astroquery.gaia import Gaia
import pandas as pd
import numpy as np

# === PATH RESOLUTION ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
CSV_PATH = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_clean_vetted.csv")
OUTPUT_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_cg22_dr3_crossmatched.csv")
MAPPING_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_dr2_dr3_mapping.csv")


if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"DR2 catalog not found at {CSV_PATH}")

# === LOAD & PARSE DR2 MEMBERS ===
df_raw = pd.read_csv(CSV_PATH, sep='\t', comment='#', dtype=str, header=0)
unit_mask = df_raw['RA_ICRS'].str.contains(r'deg|mas|yr|km/s|mag', na=False, case=False)
dr2_df = df_raw[~unit_mask].copy()

for col in ['Source', 'Proba']:
    if col in dr2_df.columns:
        dr2_df[col] = pd.to_numeric(dr2_df[col], errors='coerce')

dr2_members = dr2_df[dr2_df["Proba"] >= 0.9].dropna(subset=["Proba"]).copy()
source_ids = dr2_members["Source"].astype(int).tolist()
N_CG22 = len(source_ids)
print(f"🔗 Stage 1: Resolving {N_CG22} CG22 Pmem≥0.9 members via gaiaedr3.dr2_neighbourhood...")

# === STAGE 1: BATCHED NEIGHBOUR LOOKUP (PRESERVE DIAGNOSTICS) ===
CHUNK_SIZE = 200
neighbour_rows = []

for i in range(0, len(source_ids), CHUNK_SIZE):
    chunk = source_ids[i:i+CHUNK_SIZE]
    id_list = ','.join([str(sid) for sid in chunk])
    query = f"""
    SELECT 
        n.dr2_source_id,
        n.dr3_source_id,
        n.angular_distance
    FROM gaiaedr3.dr2_neighbourhood n
    WHERE n.dr2_source_id IN ({id_list})
    """
    job = Gaia.launch_job(query)
    result = job.get_results().to_pandas()
    neighbour_rows.append(result)
    print(f"   Chunk {i//CHUNK_SIZE + 1}/{(len(source_ids)-1)//CHUNK_SIZE + 1}: {len(result)} rows")

neighbours = pd.concat(neighbour_rows, ignore_index=True)
N_NEIGHBOURS = len(neighbours)
print(f"✅ Stage 1 complete: {N_NEIGHBOURS} total neighbour rows")

# Verify expected columns exist
EXPECTED_COLS = {'dr2_source_id', 'dr3_source_id', 'angular_distance'}
ACTUAL_COLS = set(neighbours.columns)
MISSING_COLS = EXPECTED_COLS - ACTUAL_COLS
if MISSING_COLS:
    raise KeyError(f"CRITICAL: Missing columns in neighbour results: {MISSING_COLS}. Actual: {ACTUAL_COLS}")

# === STAGE 2: DUPLICATE STATISTICS & RESOLUTION ===
multi_cases = neighbours.groupby("dr2_source_id").size()
n_multiple_sources = (multi_cases > 1).sum()
extra_rows = N_NEIGHBOURS - N_CG22

print(f"   Multiple-match sources: {n_multiple_sources}")
print(f"   Extra neighbour rows beyond minimum: {extra_rows}")

# Resolve by smallest angular_distance (methodological choice)
best_matches = neighbours.loc[
    neighbours.groupby('dr2_source_id')['angular_distance'].idxmin()
][['dr2_source_id', 'dr3_source_id', 'angular_distance']].reset_index(drop=True)

# Merge membership probabilities back
dr3_mapping = best_matches.merge(
    dr2_members[['Source', 'Proba']], 
    left_on='dr2_source_id', 
    right_on='Source'
)[['dr2_source_id', 'dr3_source_id', 'angular_distance', 'Proba']]

# Validate one-to-one DR2 mapping; report DR3 duplicates instead of asserting
assert dr3_mapping["dr2_source_id"].is_unique, "Non-unique DR2 IDs after resolution!"
duplicate_dr3 = dr3_mapping["dr3_source_id"].duplicated().sum()
print(f"   Duplicate DR3 IDs after resolution: {duplicate_dr3}")

# Validate no members lost during resolution
assert len(dr3_mapping) == N_CG22, f"Member loss detected! Expected {N_CG22}, got {len(dr3_mapping)}"
print(f"✅ One-to-one DR2 mapping verified: {len(dr3_mapping)} unique pairs")

# Compute mapping quality metrics for documentation (UNITS ARE MAS, NOT DEGREES)
ang_dist_stats = {
    'median': best_matches['angular_distance'].median(),
    'max': best_matches['angular_distance'].max(),
    'p95': best_matches['angular_distance'].quantile(0.95)
}
print(f"   Angular distance stats: median={ang_dist_stats['median']:.3f} mas, max={ang_dist_stats['max']:.3f} mas, p95={ang_dist_stats['p95']:.3f} mas")

# Show top 10 worst matches for transparency
worst_matches = best_matches.sort_values("angular_distance", ascending=False).head(10)
print(f"   Top 10 worst angular_distance matches:")
print(worst_matches[['dr2_source_id', 'dr3_source_id', 'angular_distance']].to_string(index=False))

abs_mapping = os.path.abspath(MAPPING_CSV)
dr3_mapping.to_csv(abs_mapping, index=False)
print(f"💾 Saved DR2↔DR3 mapping with diagnostics to {abs_mapping}")

# === STAGE 3: BATCHED DR3 ASTROMETRY RETRIEVAL ===
astrometry_chunks = []
dr3_ids = dr3_mapping['dr3_source_id'].tolist()
ASTRO_CHUNK_SIZE = 150  # Increased from 50 per reviewer recommendation

for i in range(0, len(dr3_ids), ASTRO_CHUNK_SIZE):
    chunk = dr3_ids[i:i+ASTRO_CHUNK_SIZE]
    id_list = ','.join([str(sid) for sid in chunk])
    print(f"Stage 3 chunk {i//ASTRO_CHUNK_SIZE + 1} starting...")
    try:
        query = f"""
        SELECT 
            g.source_id, g.ra, g.dec, g.parallax, g.parallax_error,
            g.pmra, g.pmra_error, g.pmdec, g.pmdec_error,
            g.phot_g_mean_mag, g.ruwe
        FROM gaiadr3.gaia_source g
        WHERE g.source_id IN ({id_list})
        """
        job = Gaia.launch_job(query)
        result = job.get_results().to_pandas()
        astrometry_chunks.append(result)
        print(f"Stage 3 chunk {i//ASTRO_CHUNK_SIZE + 1} finished: {len(result)} sources")
    except Exception as e:
        print(f"️ Chunk failed: {e}")
        continue

dr3_astrometry = pd.concat(astrometry_chunks, ignore_index=True)
N_RETRIEVED = len(dr3_astrometry)
N_MISSING = len(dr3_mapping) - N_RETRIEVED
print(f"✅ Retrieved DR3 astrometry: {N_RETRIEVED} ({N_MISSING} missing)")

# === SAVE RAW UNFILTERED DR3 TABLE FOR REPRODUCIBLE AUDIT ===
raw_output = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_dr3_raw.csv")
pre_quality_df = dr3_astrometry.merge(dr3_mapping, left_on='source_id', right_on='dr3_source_id')
pre_quality_df.to_csv(os.path.abspath(raw_output), index=False)
print(f"💾 Saved raw unfiltered DR3 table ({len(pre_quality_df)} stars) to {os.path.abspath(raw_output)}")

# Merge astrometry with mapping using dr3_source_id ↔ source_id
final = dr3_astrometry.merge(dr3_mapping, left_on='source_id', right_on='dr3_source_id')

# Apply TRACEBIND quality cuts
N_PRE_QUALITY = len(final)
final = final[
    (final["parallax"] > 0) &
    (final["ruwe"] < 1.4) &
    (final["phot_g_mean_mag"] < 18.0)
].copy()

if "parallax_error" in final.columns:
    final = final[final["parallax_error"] > 0].copy()
    final["plx_sn"] = final["parallax"] / final["parallax_error"]
    final = final[final["plx_sn"] > 10].copy()

final = final.dropna(subset=["parallax", "pmra", "pmdec"]).reset_index(drop=True)
N_PASSED = len(final)
N_FAILED = N_PRE_QUALITY - N_PASSED
print(f"✅ Passed TRACEBIND quality filters: {N_PASSED} ({N_FAILED} rejected)")

# Save final benchmark
abs_output = os.path.abspath(OUTPUT_CSV)
final.to_csv(abs_output, index=False)
print(f"\n💾 Saved {N_PASSED} vetted DR3 members to {abs_output}")

# === FINAL AUDIT REPORT ===
print("\n" + "=" * 60)
print("TRACEBIND PLEIADES DR3 BENCHMARK AUDIT REPORT")
print("=" * 60)
print(f"CG22 Pmem ≥ 0.9 members:                {N_CG22:>6}")
print(f"Resolved to DR3 neighbours:             {N_CG22:>6}")
print(f"Multiple-match sources:                 {n_multiple_sources:>6}")
print(f"Extra neighbour rows:                   {extra_rows:>6}")
print(f"Duplicate DR3 IDs after resolution:     {duplicate_dr3:>6}")
print(f"Retrieved DR3 astrometry:               {N_RETRIEVED:>6}")
print(f"Missing DR3 astrometry:                 {N_MISSING:>6}")
print(f"Passed TRACEBIND quality filters:       {N_PASSED:>6}")
print(f"Failed quality filters:                 {N_FAILED:>6}")
print(f"Final benchmark size:                   {N_PASSED:>6}")
print("-" * 60)
print(f"Median parallax:                        {final['parallax'].median():>6.4f} mas")
print(f"Median distance:                        {(1000.0/final['parallax']).median():>6.2f} pc")
print(f"Median RUWE:                            {final['ruwe'].median():>6.3f}")
print(f"Median G magnitude:                     {final['phot_g_mean_mag'].median():>6.2f}")
print(f"Mapping ang_dist median:                {ang_dist_stats['median']:>6.3f} mas")
print(f"Mapping ang_dist max:                   {ang_dist_stats['max']:>6.3f} mas")
print(f"Mapping ang_dist p95:                   {ang_dist_stats['p95']:>6.3f} mas")
print("=" * 60)
print("⚠️  NOTE: Final sample ≠ CG22 published catalogue.")
print("   Quality cuts (RUWE<1.4, G<18, plx_sn>10) reduce membership.")
print("   This is the TRACEBIND analysis sample, not the original CG22 set.")
print("=" * 60)