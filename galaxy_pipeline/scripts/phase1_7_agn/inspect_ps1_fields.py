import requests
import pandas as pd
import io

# Coordinates for Gaia DR3 4575090461821845760
ra = 257.312761
dec = 28.446286

print(" INSPECTING PAN-STARRS DR2 SCHEMA\n" + "="*50)

url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
params = {"ra": ra, "dec": dec, "radius": 0.001} # 3.6 arcsec

try:
    response = requests.get(url, params=params, timeout=10)
    
    if response.ok:
        # Filter out comment lines (#) which MAST includes in CSV headers
        text = '\n'.join([line for line in response.text.split('\n') if not line.startswith('#')])
        
        if text.strip():
            df = pd.read_csv(io.StringIO(text))
            
            if len(df) > 0:
                row = df.iloc[0]
                obj_id = row.get('objID', 'Unknown')
                
                print(f"✅ MATCHED OBJECT: {obj_id}")
                print(f"📊 DUMPING ALL AVAILABLE FIELDS:\n")
                
                # Print every column and its value to see exactly what the API returns
                for col in df.columns:
                    print(f"  {col:25s} : {row[col]}")
                    
                # Recalculate extension to be absolutely sure
                print("\n" + "="*50)
                if 'gMeanPSFMag' in df.columns and 'gMeanKronMag' in df.columns:
                    print("EXTENSION CHECK (Recalculated):")
                    ext_g = row['gMeanPSFMag'] - row['gMeanKronMag']
                    ext_r = row['rMeanPSFMag'] - row['rMeanKronMag']
                    print(f"  g-band Delta (PSF-Kron): {ext_g:.3f}")
                    print(f"  r-band Delta (PSF-Kron): {ext_r:.3f}")
                    
                    if ext_g > 0.5 or ext_r > 0.5:
                        print("  👉 VERDICT: DEFINITELY EXTENDED")
                    else:
                        print("   VERDICT: POINT SOURCE")
            else:
                print("⚠️ No object found in this radius.")
        else:
            print("⚠️ Empty response from API.")
    else:
        print(f"❌ Request failed with status {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")