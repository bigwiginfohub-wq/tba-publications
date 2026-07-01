import pandas as pd
import requests
import io
import time
from astroquery.gaia import Gaia
import warnings
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
INPUT_FILE = "tight_candidates.csv"  # Change if your file is named differently
OUTPUT_FILE = "batch_ranked_candidates.csv"

print("🔍 BATCH EXTRAGALACTIC VALIDATION PIPELINE\n" + "="*60)

try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"❌ {INPUT_FILE} not found. Ensure your candidate list exists in the project folder.")
    exit()

results = []
total = len(df)

for idx, row in df.iterrows():
    src_id = row['source_id']
    ra, dec = row['ra'], row['dec']
    print(f"[{idx+1}/{total}] Processing {src_id}...")

    score = 0
    notes = []
    gaia_snr = "N/A"
    ps1_ext = "N/A"
    ps1_color = "N/A"

    # 1. GAIA ASTROMETRY CHECK
    try:
        query = f"""
        SELECT parallax, parallax_error, pmra, pmra_error, pmdec, pmdec_error
        FROM gaiadr3.gaia_source WHERE source_id = {src_id}
        """
        job = Gaia.launch_job(query)
        g_res = job.get_results()
        if len(g_res) > 0:
            g = g_res[0]
            plx_snr = abs(g['parallax']) / g['parallax_error'] if g['parallax_error'] > 0 else 0
            pm_snr = max(
                abs(g['pmra']) / g['pmra_error'] if g['pmra_error'] > 0 else 0,
                abs(g['pmdec']) / g['pmdec_error'] if g['pmdec_error'] > 0 else 0
            )
            gaia_snr = f"P={plx_snr:.1f}, PM={pm_snr:.1f}"
            
            if plx_snr < 3 and pm_snr < 3:
                score += 2; notes.append("Gaia: Extragalactic astrometry")
            elif plx_snr > 5 or pm_snr > 5:
                score -= 2; notes.append("Gaia: Stellar motion/parallax")
        else:
            notes.append("Gaia: No data")
    except Exception as e:
        notes.append(f"Gaia query failed")

    time.sleep(1.5)  # Respect Gaia rate limit

    # 2. PAN-STARRS MORPHOLOGY & COLORS
    try:
        url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
        params = {"ra": ra, "dec": dec, "radius": 0.001}  # ~3.6 arcsec
        r = requests.get(url, params=params, timeout=10)
        
        if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
            lines = [l for l in r.text.split('\n') if not l.startswith('#')]
            if lines:
                ps1 = pd.read_csv(io.StringIO('\n'.join(lines)))
                if len(ps1) > 0:
                    p = ps1.iloc[0]
                    
                    # Check required columns exist
                    if all(c in ps1.columns for c in ['gMeanPSFMag', 'gMeanKronMag', 'rMeanPSFMag', 'rMeanKronMag']):
                        g_ext = p['gMeanPSFMag'] - p['gMeanKronMag']
                        r_ext = p['rMeanPSFMag'] - p['rMeanKronMag']
                        max_ext = max(g_ext, r_ext)
                        gr_color = p['gMeanPSFMag'] - p['rMeanPSFMag']
                        
                        ps1_ext = f"Δ={max_ext:.2f}"
                        ps1_color = f"g-r={gr_color:.2f}"

                        if max_ext > 0.5:
                            score += 2; notes.append(f"PS1: Extended (Δ={max_ext:.2f})")
                        elif max_ext < 0.1:
                            score -= 2; notes.append("PS1: Point source")

                        if gr_color < 0.5:
                            score += 1; notes.append("PS1: Blue color")
                    else:
                        notes.append("PS1: Missing magnitude columns")
            else:
                notes.append("PS1: No match")
    except Exception as e:
        notes.append("PS1: API error")

    time.sleep(1.5)  # Respect MAST rate limit

    results.append({
        'source_id': src_id,
        'ra': ra,
        'dec': dec,
        'gaia_astrometry_snr': gaia_snr,
        'ps1_extension': ps1_ext,
        'ps1_color': ps1_color,
        'priority_score': score,
        'diagnostic_notes': '; '.join(notes)
    })

# ──────────────────────────────────────────────────────────────
# SAVE & DISPLAY RESULTS
# ──────────────────────────────────────────────────────────────
out_df = pd.DataFrame(results)
out_df['rank'] = out_df['priority_score'].rank(method='min', ascending=False).astype(int)
out_df = out_df.sort_values('priority_score', ascending=False)

out_df.to_csv(OUTPUT_FILE, index=False)

print("\n" + "="*60)
print("✅ BATCH COMPLETE")
print(f"📁 Results saved to: {OUTPUT_FILE}")
print("\n🏆 TOP 10 RANKED CANDIDATES:")
print(out_df.head(10).to_string(index=False))