import requests
import pandas as pd
import io

ra, dec = 257.312761, 28.446286
# Correct Legacy Survey DR10 Catalog Search API
url = f"https://legacysurvey.org/dr10/catalogs/search/?ra={ra}&dec={dec}&radius=0.001&rowlimit=5&format=csv"

print(" Querying Legacy Survey DR10 Catalog Search API...\n")
r = requests.get(url, timeout=10)

if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
    try:
        # Skip metadata/comments
        df = pd.read_csv(io.StringIO(r.text), comment='#')
        
        if len(df) > 0:
            print("✅ LEGACY SURVEY DR10 OBJECT DATA:")
            cols = ['ls_id', 'type', 'g', 'r', 'z', 'phot_z']
            existing = [c for c in cols if c in df.columns]
            print(df[existing].to_string(index=False))
            
            if 'type' in df.columns:
                print(f"\n👉 MORPHOLOGY TYPE: {df['type'].values[0].upper()}")
                print("   PSF = Point Source (Star/Quasar)")
                print("   REX/EXP/DEV = Resolved/Galaxy")
        else:
            print("⚠️ No cataloged object found within ~3.6 arcseconds.")
    except Exception as e:
        print(f"❌ Parse error: {e}")
else:
    print("❌ API returned non-CSV data. Raw response preview:")
    print(r.text[:200].replace('\n', ' '))