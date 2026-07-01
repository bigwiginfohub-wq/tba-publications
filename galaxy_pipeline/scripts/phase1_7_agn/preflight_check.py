from astroquery.gaia import Gaia
print("🔍 Checking Gaia DR3 DSC classifier availability...")
query = """
SELECT TOP 1 
classprob_dsc_combmod_star, 
classprob_dsc_combmod_galaxy, 
classprob_dsc_combmod_quasar
FROM gaiadr3.gaia_source
"""
try:
    job = Gaia.launch_job(query)
    res = job.get_results()
    print("✅ DSC columns available. Pipeline will use them.")
    print(f"   Example values: Star={res[0]['classprob_dsc_combmod_star']:.2e}, Galaxy={res[0]['classprob_dsc_combmod_galaxy']:.2e}")
except Exception as e:
    print("⚠️ DSC columns unavailable in this archive view. Pipeline will fall back to astrometry-only scoring.")
    print(f"   Error: {e}")