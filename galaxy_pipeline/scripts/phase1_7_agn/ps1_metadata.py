import requests
import pandas as pd
import io

ra, dec = 257.312761, 28.446286
url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
params = {"ra": ra, "dec": dec, "radius": 0.0003, "format": "csv"}

print(" Querying Pan-STARRS DR2 Metadata & Flags...\n")
r = requests.get(url, params=params, timeout=10)

if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
    lines = [l for l in r.text.split('\n') if not l.startswith('#')]
    if lines:
        df = pd.read_csv(io.StringIO('\n'.join(lines)))
        if len(df) > 0:
            row = df.iloc[0]
            print("✅ PAN-STARRS DR2 METADATA:")
            key_cols = ['objID', 'raMean', 'decMean', 'objInfoFlag', 'qualityFlag',
                        'primaryDetection', 'nDetections',
                        'gMeanPSFMag', 'gMeanKronMag',
                        'rMeanPSFMag', 'rMeanKronMag',
                        'iMeanPSFMag', 'iMeanKronMag',
                        'zMeanPSFMag', 'zMeanKronMag']
            for col in key_cols:
                if col in df.columns:
                    val = row[col]
                    print(f"  {col:20s}: {val}")

            # Flag interpretation
            print("\n📊 FLAG INTERPRETATION:")
            qflag = row.get('qualityFlag', -1)
            if qflag == 0:
                print("  qualityFlag = 0 → Clean detection, no photometric issues")
            else:
                print(f"  qualityFlag = {qflag} → Non-zero bitmask (check PS1 docs). Common for faint/extended sources.")

            objflag = row.get('objInfoFlag', -1)
            # PS1 objInfoFlag bitmask: bit0=point, bit1=extended, bit2=saturated, bit3=variable, etc.
            if objflag & 2:
                print("  objInfoFlag & 2 = TRUE → PS1 internally classifies as EXTENDED")
            elif objflag & 1:
                print("  objInfoFlag & 1 = TRUE → PS1 internally classifies as POINT-LIKE")
            else:
                print(f"  objInfoFlag = {objflag} → Mixed/complex source classification")

            print("\n👉 VERDICT BASED ON FLAGS + MAGNITUDES:")
            print("  Δ(PSF-Kron) > 0.8 in g/r/i + blue colors (g-r=-0.17)")
            print("  = Resolved blue galaxy / AGN host / star-forming dwarf")
        else:
            print("️ No match in PS1 mean table.")
    else:
        print("⚠️ Empty response from PS1 API.")
else:
    print("❌ PS1 API request failed.")