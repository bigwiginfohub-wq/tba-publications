import requests
import pandas as pd
import numpy as np
import io
import time

# Your 5 survivors from batch_filter.py
survivors = [
    {"id": 6158874323829427200, "ra": 192.109396, "dec": -34.116281},
    {"id": 4575090461821845504, "ra": 257.312761, "dec": 28.446286},
    {"id": 3663219731798361600, "ra": 204.992453, "dec": 0.834006},
    {"id": 4921284891965816832, "ra": 14.493363, "dec": -53.200202},
    {"id": 2374402820540535808, "ra": 9.785671, "dec": -14.174743}
]

results = []
print("🔍 Running WISE + Pan-STARRS Morphology Scorer\n" + "="*60)

for cand in survivors:
    print(f"\n📡 Processing {cand['id']} | RA={cand['ra']:.4f} DEC={cand['dec']:.4f}")
    score = 0
    wise_w1, wise_w2 = np.nan, np.nan
    ext = 0.0
    wise_flag = "NO DATA"
    ps1_flag = "NO DATA"

    # 1. WISE AllWISE Cross-Match (3" radius)
    try:
        wise_url = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"
        wise_params = {"catalog": "wise_allwise_p3as_psd", "RA": cand["ra"], "DEC": cand["dec"],
                       "SR": "3", "outfmt": "csv", "outcols": "ra,dec,w1mpro,w2mpro,w3mpro"}
        r = requests.get(wise_url, params=wise_params, timeout=10)
        if r.ok and "w1mpro" in r.text:
            wise_df = pd.read_csv(io.StringIO(r.text), comment='#')
            if len(wise_df) > 0:
                row = wise_df.iloc[0]
                wise_w1, wise_w2, w3 = row["w1mpro"], row["w2mpro"], row["w3mpro"]
                w1_w2 = wise_w1 - wise_w2
                if w1_w2 > 0.8: score += 2; wise_flag = "AGN/GALAXY IR"
                elif w1_w2 > 0.3: score += 1; wise_flag = "POSSIBLE GALAXY"
                else: score -= 2; wise_flag = "STELLAR IR"
    except Exception as e:
        wise_flag = f"API ERROR ({str(e)[:25]})"

    # 2. Pan-STARRS DR2 Cross-Match (~1" radius)
    try:
        ps1_url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
        ps1_params = {"ra": cand["ra"], "dec": cand["dec"], "radius": 0.0003, "nDetections.gt": 1}
        r = requests.get(ps1_url, params=ps1_params, timeout=10)
        if r.ok and r.text.strip():
            ps1_df = pd.read_csv(io.StringIO(r.text))
            if len(ps1_df) > 0:
                row = ps1_df.iloc[0]
                g_psf = row.get("gMeanPSFMag", np.nan)
                g_kron = row.get("gMeanKronMag", np.nan)
                r_psf = row.get("rMeanPSFMag", np.nan)
                r_kron = row.get("rMeanKronMag", np.nan)
                ext = max(g_psf - g_kron if not np.isnan(g_psf) else 0,
                          r_psf - r_kron if not np.isnan(r_psf) else 0)
                if ext > 0.10: score += 2; ps1_flag = "STRONGLY EXTENDED"
                elif ext > 0.05: score += 1; ps1_flag = "MODERATELY EXTENDED"
                else: score -= 2; ps1_flag = "POINT SOURCE"
    except Exception as e:
        ps1_flag = f"API ERROR ({str(e)[:25]})"

    results.append({
        "source_id": cand["id"], "ra": cand["ra"], "dec": cand["dec"],
        "WISE_W1-W2": round(wise_w1 - wise_w2, 3) if not np.isnan(wise_w1) else "N/A",
        "WISE_Flag": wise_flag,
        "PS1_Extendedness": round(ext, 3),
        "PS1_Flag": ps1_flag,
        "Priority_Score": score
    })
    time.sleep(1.5)  # Respect API rate limits

# Save & display
out_df = pd.DataFrame(results).sort_values("Priority_Score", ascending=False)
out_df.to_csv("final_ranked_survivors.csv", index=False)

print("\n" + "="*60)
print("✅ SCORING COMPLETE")
print(out_df.to_string(index=False))
print("\n📁 Saved to final_ranked_survivors.csv")