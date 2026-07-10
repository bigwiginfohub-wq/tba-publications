"""Cross-match Pleiades DR2 members to Gaia DR3 via official neighbour table."""
import os
import tempfile
from astroquery.gaia import Gaia
import pandas as pd
import numpy as np

# Resolve paths relative to project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
CSV_PATH = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_clean_vetted.csv")
OUTPUT_CSV = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_cg22_dr3_crossmatched.csv")

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"DR2 catalog not found at {CSV_PATH}")

# Load and parse DR2 members safely
df_raw = pd.read_csv(CSV_PATH, sep='\t', comment='#', dtype=str, header=0)
unit_mask = df_raw['RA_ICRS'].str.contains(r'deg|mas|yr|km/s|mag', na=False, case=False)
dr2_df = df_raw[~unit_mask].copy()

numeric_cols = ['Source', 'Proba']
for col in numeric_cols:
    if col in dr2_df.columns:
        dr2_df[col] = pd.to_numeric(dr2_df[col], errors='coerce')

dr2_members = dr2_df[dr2_df["Proba"] >= 0.9].dropna(subset=["Proba"]).copy()
print(f"🔗 Cross-matching {len(dr2_members)} DR2 members via official neighbour table...")

# Write upload table to temp file (avoids API signature issues)
upload_df = dr2_members[["Source", "Proba"]].copy()
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
    upload_df.to_csv(tmp.name, index=False)
    tmp_path = tmp.name

try:
    # Upload using FILE PATH STRING (compatible with astroquery 0.4.11)
    job_upload = Gaia.upload_table(
        upload_resource=tmp_path,
        table_name="uploaded_pleiades_dr2",
        format="csv"
    )
    print(f"✅ Uploaded {len(upload_df)} DR2 members as user table")
finally:
    os.unlink(tmp_path)

# Execute cross-match via official gaiaedr3.dr2_neighbourhood table
# This accounts for proper motion propagation between DR2 (2015.5) and DR3 (2016.0)
query = """
SELECT 
    n.source_id AS dr3_source_id,
    n.dr2_source_id AS dr2_source_id,
    g.ra, g.dec, g.parallax, g.parallax_error,
    g.pmra, g.pmra_error, g.pmdec, g.pmdec_error,
    g.phot_g_mean_mag, g.ruwe,
    u.Proba AS member_prob
FROM gaiaedr3.dr2_neighbourhood n
INNER JOIN gaiadr3.gaia_source g ON n.source_id = g.source_id
INNER JOIN uploaded_pleiades_dr2 u ON n.dr2_source_id = u.Source
WHERE g.ruwe < 1.4 AND g.phot_g_mean_mag < 18.0
"""

job = Gaia.launch_job(query)
dr3_crossmatch = job.get_results().to_pandas()
print(f"✅ Cross-matched {len(dr3_crossmatch)} sources via official neighbour table")

# Apply standard TRACEBIND quality cuts
dr3_crossmatch = dr3_crossmatch[
    (dr3_crossmatch["parallax"] > 0) &
    (dr3_crossmatch["ruwe"] < 1.4) &
    (dr3_crossmatch["phot_g_mean_mag"] < 18.0)
].copy()

if "parallax_error" in dr3_crossmatch.columns:
    dr3_crossmatch = dr3_crossmatch[dr3_crossmatch["parallax_error"] > 0].copy()
    dr3_crossmatch["plx_sn"] = dr3_crossmatch["parallax"] / dr3_crossmatch["parallax_error"]
    dr3_crossmatch = dr3_crossmatch[dr3_crossmatch["plx_sn"] > 10].copy()

dr3_crossmatch = dr3_crossmatch.dropna(subset=["parallax", "pmra", "pmdec"]).reset_index(drop=True)

# Save as frozen DR3 benchmark
abs_output = os.path.abspath(OUTPUT_CSV)
dr3_crossmatch.to_csv(abs_output, index=False)
print(f"\n💾 Saved {len(dr3_crossmatch)} vetted DR3 members to {abs_output}")
print(f"   Median distance: {(1000.0 / dr3_crossmatch['parallax']).median():.2f} pc")
print(f"   Median parallax: {dr3_crossmatch['parallax'].median():.4f} mas")