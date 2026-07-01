import requests
import pandas as pd
import numpy as np
import io
import time

targets = [
    {"id": 2374402820540535808, "ra": 9.785671, "dec": -14.174743},
    {"id": 6158874323829427200, "ra": 192.109396, "dec": -34.116281}
]

print("🌡️ WISE ALLWISE DEEP CHECK\n" + "="*60)
for t in targets:
    print(f"\n Target: {t['id']} | RA={t['ra']} DEC={t['dec']}")
    url = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"
    # SR=0.0014 degrees ≈ 5 arcseconds
    params = {"catalog": "wise_allwise_p3as_psd", "RA": t["ra"], "DEC": t["dec"],
              "SR": "0.0014", "outfmt": "csv", "outcols": "ra,dec,w1mpro,w2mpro,w3mpro,w4mpro"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.ok and "w1mpro" in r.text:
            df = pd.read_csv(io.StringIO(r.text), comment='#')
            if len(df) > 0:
                row = df.iloc[0]
                w1, w2, w3, w4 = row["w1mpro"], row["w2mpro"], row["w3mpro"], row["w4mpro"]
                w1_w2 = w1 - w2
                w2_w3 = w2 - w3
                print(f"  W1: {w1:.2f} | W2: {w2:.2f} | W3: {w3:.2f} | W4: {w4:.2f}")
                print(f"  W1-W2: {w1_w2:.2f} | W2-W3: {w2_w3:.2f}")
                if w1_w2 > 0.8: print("  🚩 AGN/Galaxy IR Signature")
                elif w1_w2 < 0.2: print("  ⭐ Stellar IR Signature")
                else: print("  ⚠️ Intermediate/Composite IR")
            else:
                print("  ⚠️ No WISE source within 5\"")
        else:
            print("  ⚠️ No WISE data returned")
    except Exception as e:
        print(f"  ❌ WISE API Error")
    time.sleep(1.5)