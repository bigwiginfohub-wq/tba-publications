import requests
import pandas as pd
import numpy as np
import io

ra, dec = 257.312761, 28.446286
url = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"
params = {
    "catalog": "wise_allwise_p3as_psd",
    "RA": ra, "DEC": dec,
    "SR": "0.0014",  # ~5 arcseconds
    "outfmt": "csv",
    "outcols": "ra,dec,w1mpro,w2mpro,w3mpro,w4mpro"
}

print("🔍 Querying WISE AllWISE Photometry (5\" radius)...\n")
r = requests.get(url, params=params, timeout=10)

if r.ok and "w1mpro" in r.text:
    try:
        # Skip IRSA comment lines (#)
        lines = [l for l in r.text.split('\n') if not l.startswith('#')]
        df = pd.read_csv(io.StringIO('\n'.join(lines)))
        if len(df) > 0:
            row = df.iloc[0]
            w1, w2 = row["w1mpro"], row["w2mpro"]
            w1_w2 = w1 - w2
            
            print("✅ WISE AllWISE PHOTOMETRY:")
            print(f"  W1 (3.4μm): {w1:.3f}")
            print(f"  W2 (4.6μm): {w2:.3f}")
            print(f"  W1-W2:      {w1_w2:.3f}")
            
            print("\n📊 AGN SELECTION DIAGNOSTIC (Stern et al. 2012):")
            if w1_w2 > 0.8:
                print("  🔴 W1-W2 > 0.8 → Strong AGN/QSO indicator")
                print("     → Power-law IR continuum from hot dust near SMBH")
            elif w1_w2 > 0.3:
                print("   W1-W2 > 0.3 → Possible AGN or star-forming galaxy")
                print("     → Requires optical follow-up for confirmation")
            else:
                print("  🔵 W1-W2 < 0.3 → Likely stellar or passive galaxy")
                print("     → Does not match QSO/AGN IR signature")
        else:
            print("⚠️ No WISE source within ~5\". (Likely below WISE detection limit)")
    except Exception as e:
        print(f"❌ Parse error: {e}")
else:
    print("❌ WISE API returned no data or HTML.")