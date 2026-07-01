import requests
import pandas as pd
import numpy as np
import io
import time

candidates = [
    {"id": 6158874323829427200, "ra": 192.109396, "dec": -34.116281},
    {"id": 4921284891965816832, "ra": 14.493363, "dec": -53.200202}
]

print("🌡️ WISE ALLWISE IR CHECK (18\" RADIUS)\n" + "="*60)
for c in candidates:
    print(f"\n🆔 {c['id']}")
    url = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"
    params = {
        "catalog": "wise_allwise_p3as_psd",
        "RA": c["ra"], "DEC": c["dec"],
        "SR": "0.005",  # ~18 arcseconds
        "outfmt": "csv",
        "outcols": "ra,dec,w1mpro,w2mpro,w3mpro"
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.ok and "w1mpro" in r.text:
            df = pd.read_csv(io.StringIO(r.text), comment='#')
            if len(df) > 0:
                row = df.iloc[0]
                w1, w2, w3 = row["w1mpro"], row["w2mpro"], row["w3mpro"]
                print(f"  W1={w1:.2f} | W2={w2:.2f} | W3={w3:.2f}")
                print(f"  W1-W2 = {w1-w2:.2f} | W2-W3 = {w2-w3:.2f}")
                if w1-w2 > 0.8: print("  🚩 AGN/Galaxy IR Excess")
                elif w1-w2 < 0.2: print("  ⭐ Stellar IR Signature")
                else: print("  ⚠️ Intermediate/Composite")
            else:
                print("  ⚠️ No WISE source within 18\"")
        else:
            print("  ⚠️ No WISE data returned (check IRSA manually)")
    except Exception as e:
        print(f"  ❌ API Error: {str(e)[:40]}")
    time.sleep(1.5)