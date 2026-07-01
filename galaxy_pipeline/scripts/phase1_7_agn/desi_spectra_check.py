from astroquery.vizier import Vizier
import time

ra, dec = 257.312761, 28.446286
print("🔍 Querying DESI Spectroscopic Catalogs (5\" radius)...\n")

# Columns we care about
viz = Vizier(columns=["TargetID", "RA", "DEC", "Z", "ZWARN", "Spectype", "Target"], row_limit=10)
found = False

# DESI DR1 (J/ApJS/270/26) and EDR (J/ApJS/267/15)
for cat in ["J/ApJS/270/26", "J/ApJS/267/15"]:
    try:
        res = viz.query_region(f"{ra},{dec}", radius="5s", catalog=[cat])
        if res and len(res[cat]) > 0:
            print(f"✅ MATCH FOUND in {cat}:")
            print(res[cat][["TargetID", "Z", "ZWARN", "Spectype", "Target"]].to_string(index=False))
            found = True
            break
    except Exception as e:
        print(f"⚠️ {cat} query skipped: {str(e)[:40]}")
    time.sleep(1.5)

if not found:
    print(" No spectroscopic match in DESI DR1/EDR within 5\".")
    print("   → Object may be a targeting-only candidate (not yet observed),")
    print("     or lies in a gap between DESI tiles.")
    print("\n🔗 MANUAL DESI SPECTRA CHECK:")
    print(f"https://legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&pixscale=0.262&bands=grz")