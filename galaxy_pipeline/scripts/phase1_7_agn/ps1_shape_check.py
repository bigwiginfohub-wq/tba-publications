import requests
import pandas as pd
import numpy as np
import io

ra, dec = 257.312761, 28.446286
url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
params = {"ra": ra, "dec": dec, "radius": 0.0003, "format": "csv"}

print("🔍 PAN-STARRS DR2 SHAPE & FLAGS\n" + "="*50)
r = requests.get(url, params=params, timeout=10)

if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
    lines = [l for l in r.text.split('\n') if not l.startswith('#')]
    if lines:
        df = pd.read_csv(io.StringIO('\n'.join(lines)))
        if len(df) > 0:
            row = df.iloc[0]
            print("✅ SHAPE & FLAG METADATA:")
            cols = ['objID', 'nDetections', 'qualityFlag', 'objInfoFlag',
                    'momentXX', 'momentYY', 'momentXY']
            for c in cols:
                if c in df.columns:
                    print(f"  {c:15s}: {row[c]}")

            # Compute ellipticity if moments exist
            if 'momentXX' in df.columns:
                mxx, myy, mxy = row['momentXX'], row['momentYY'], row['momentXY']
                if all(not np.isnan(v) for v in [mxx, myy, mxy]):
                    size = np.sqrt(mxx + myy)
                    ellip = np.sqrt((mxx-myy)**2 + 4*mxy**2) / (mxx+myy)
                    print(f"\n  📐 Derived: Size≈{size:.2f} | Ellipticity≈{ellip:.2f}")
                    print("  Ellipticity > 0.3 → Non-circular/extended structure")
        else:
            print("⚠️ No PS1 match in mean table.")
    else:
        print("⚠️ Empty PS1 response.")
else:
    print("❌ PS1 API failed.")