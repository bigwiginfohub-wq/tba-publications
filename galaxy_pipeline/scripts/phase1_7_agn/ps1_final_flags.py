import requests
import pandas as pd
import io

ra, dec = 257.312761, 28.446286
url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
params = {"ra": ra, "dec": dec, "radius": 0.0003}

print("🔍 Querying Pan-STARRS Final Flags & Morphology...\n")
r = requests.get(url, params=params, timeout=10)

if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
    lines = [l for l in r.text.split('\n') if not l.startswith('#')]
    if lines:
        df = pd.read_csv(io.StringIO('\n'.join(lines)))
        if len(df) > 0:
            row = df.iloc[0]
            print("✅ PAN-STARRS FINAL METADATA:")
            
            # Core Flags
            print(f"  objID:          {row['objID']}")
            print(f"  primaryDetection: {row['primaryDetection']}")
            print(f"  nDetections:      {row['nDetections']}")
            
            # Morphology Flags
            flag = int(row['objInfoFlag'])
            print(f"  objInfoFlag:    {flag}")
            
            # Decoding objInfoFlag (Bitmask)
            # Bit 0: Star-like
            # Bit 1: Extended/Galaxy-like
            if flag & 2:
                print("  👉 FLAG DECODE: EXTENDED (Galaxy-like)")
            elif flag & 1:
                print("   FLAG DECODE: POINT-LIKE (Star-like)")
            else:
                print("  👉 FLAG DECODE: UNCLASSIFIED/MIXED")
                
            # Quality
            qflag = row['qualityFlag']
            print(f"  qualityFlag:    {qflag} (0 = Clean)")
            
            # Reiterate the Extension (The Smoking Gun)
            g_ext = row['gMeanPSFMag'] - row['gMeanKronMag']
            print(f"\n  🔒 FINAL MORPHOLOGY CHECK:")
            print(f"  g-band Extension (PSF-Kron): {g_ext:.3f}")
            if g_ext > 0.5:
                print("  VERDICT: DEFINITELY EXTENDED GALAXY")
            else:
                print("  VERDICT: POINT SOURCE")
        else:
            print("⚠️ No match found.")
    else:
        print("️ Empty response.")
else:
    print("❌ API Request failed.")