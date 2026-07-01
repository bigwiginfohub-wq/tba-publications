from astroquery.gaia import Gaia
import time

# We will use the ID that definitely returned data in your coord search
source_id = 4575090461821845760

print(f" Querying Gaia Internal Tables for Source: {source_id}\n")

# Query 1: QSO Candidates
print("📡 1. Querying gaiadr3.qso_candidates...")
query1 = f"""
SELECT source_id, class_prob, redshift
FROM gaiadr3.qso_candidates
WHERE source_id = {source_id}
"""
try:
    job1 = Gaia.launch_job(query1)
    res1 = job1.get_results()
    if len(res1) > 0:
        print("✅ FOUND IN QSO_CANDIDATES:")
        print(res1)
    else:
        print("   ⚠️ Not found (Gaia does not classify as QSO)")
except Exception as e:
    print(f"   ❌ Error: {e}")

time.sleep(2)

# Query 2: Astrophysical Parameters
print("\n📡 2. Querying gaiadr3.astrophysical_parameters...")
query2 = f"""
SELECT source_id, teff_val, logg_val, distance_val, ag_val
FROM gaiadr3.astrophysical_parameters
WHERE source_id = {source_id}
"""
try:
    job2 = Gaia.launch_job(query2)
    res2 = job2.get_results()
    if len(res2) > 0:
        print("✅ FOUND IN ASTROPHYSICAL_PARAMETERS:")
        print(res2)
    else:
        print("   ⚠️ Not found (No stellar parameters derived, consistent with galaxy)")
except Exception as e:
    print(f"   ❌ Error: {e}")