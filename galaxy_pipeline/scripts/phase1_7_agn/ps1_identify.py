import requests
import pandas as pd
import io

ra, dec = 204.99245343657478, 0.8340056183165048
url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
params = {"ra": ra, "dec": dec, "radius": 0.003, "nDetections.gt": 1}

print("Querying Pan-STARRS DR2 via MAST API...\n")
r = requests.get(url, params=params)
print(f"Request URL: {r.url}")

if r.ok and r.text.strip():
    df = pd.read_csv(io.StringIO(r.text))
    print("\n✅ PAN-STARRS MATCHES:")
    cols = ['objID', 'raMean', 'decMean', 'type', 'gMeanPSFMag', 'rMeanPSFMag', 'photoz']
    print(df[[c for c in cols if c in df.columns]])
else:
    print("⚠️ No Pan-STARRS objects found.")