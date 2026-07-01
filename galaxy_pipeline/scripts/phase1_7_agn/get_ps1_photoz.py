import requests
import pandas as pd
import io

ra, dec = 257.312761, 28.446286
url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
# Request photo-z columns
params = {"ra": ra, "dec": dec, "radius": 0.0003, "format": "csv", 
          "columns": "objID,raMean,decMean,photoz,photozErr"}

r = requests.get(url, params=params, timeout=10)
if r.ok and r.text.strip():
    lines = [l for l in r.text.split('\n') if not l.startswith('#')]
    if lines:
        df = pd.read_csv(io.StringIO('\n'.join(lines)))
        if len(df) > 0 and 'photoz' in df.columns:
            print(f"PS1 Photo-z: {df['photoz'].iloc[0]:.3f} ± {df['photozErr'].iloc[0]:.3f}")
        else:
            print("️ No photo-z estimate available (common for faint/extended sources)")