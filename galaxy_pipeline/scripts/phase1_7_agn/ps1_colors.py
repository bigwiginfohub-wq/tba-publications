import requests
import pandas as pd
import numpy as np
import io

ra, dec = 257.312761, 28.446286
url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
params = {"ra": ra, "dec": dec, "radius": 0.001}  # 0.001 deg ≈ 3.6 arcsec

print("🔍 Querying Pan-STARRS DR2 Mean Object Catalog...\n")
r = requests.get(url, params=params, timeout=10)

if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
    try:
        # Skip metadata/comment lines
        lines = [l for l in r.text.split('\n') if not l.startswith('#')]
        if lines:
            df = pd.read_csv(io.StringIO('\n'.join(lines)))
            if len(df) > 0:
                row = df.iloc[0]
                bands = ['g', 'r', 'i', 'z', 'y']
                mags = {}
                for b in bands:
                    col = f"{b}MeanPSFMag"
                    mags[b] = row[col] if col in df.columns else np.nan

                print("✅ PAN-STARRS DR2 PHOTOMETRY:")
                for b, m in mags.items():
                    print(f"  {b}-band PSF: {m:.3f}" if not np.isnan(m) else f"  {b}-band PSF: NaN")

                # Compute colors
                colors = {}
                pairs = [('g-r', 'g', 'r'), ('r-i', 'r', 'i'), ('i-z', 'i', 'z'), ('z-y', 'z', 'y')]
                for cname, b1, b2 in pairs:
                    if not np.isnan(mags[b1]) and not np.isnan(mags[b2]):
                        colors[cname] = mags[b1] - mags[b2]

                print("\n🎨 COMPUTED COLORS:")
                for c, val in colors.items():
                    print(f"  {c}: {val:.3f}")

                # Classification mapping
                print("\n📊 COLOR-COLOR CLASSIFICATION:")
                if 'g-r' in colors and 'r-i' in colors:
                    gr, ri = colors['g-r'], colors['r-i']
                    if gr < 0.45 and ri < 0.45:
                        print("  👉 BLUE/FLAT LOCUS → Consistent with QSO or hot star")
                    elif gr > 0.85 or ri > 0.75:
                        print("  👉 RED LOCUS → Consistent with galaxy or cool star")
                    else:
                        print("  👉 INTERMEDIATE → Overlap region (QSO/Galaxy/Star)")
                    
                    # Cross-check with i-z
                    if 'i-z' in colors:
                        iz = colors['i-z']
                        if iz > 0.6:
                            print("  🔴 High i-z → Strongly favors Galaxy (Balmer break/4000Å)")
                        elif iz < 0.3:
                            print("  🔵 Low i-z → Favors QSO or blue star")
                else:
                    print("  ⚠️ Insufficient bands for color calculation.")
                    
            else:
                print("⚠️ No PS1 match found within 3.6\".")
        else:
            print("⚠️ Empty response from PS1 API.")
    except Exception as e:
        print(f"❌ Parse error: {e}")
else:
    print("❌ API request failed or returned HTML.")