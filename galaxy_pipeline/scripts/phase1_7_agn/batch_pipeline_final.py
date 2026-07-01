import pandas as pd
import requests
import io
import time
import os
import math
from astroquery.gaia import Gaia
import warnings
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
INPUT_FILE = "tight_candidates.csv"
OUTPUT_FILE = "batch_ranked_candidates.csv"
CHECKPOINT_FILE = "batch_checkpoint.pkl"

print("🔍 FINAL BATCH EXTRAGALACTIC VALIDATION PIPELINE\n" + "="*60)

if not os.path.exists(INPUT_FILE):
    print(f"❌ {INPUT_FILE} not found.")
    exit()

df = pd.read_csv(INPUT_FILE)

# Load checkpoint
if os.path.exists(CHECKPOINT_FILE):
    print("📂 Resuming from checkpoint...")
    checkpoint = pd.read_pickle(CHECKPOINT_FILE)
    processed_ids = set(checkpoint['source_id'].tolist())
    results = checkpoint.to_dict('records')
    df = df[~df['source_id'].isin(processed_ids)]
else:
    results = []

total = len(df) + len(results)
current = len(results) + 1

# ──────────────────────────────────────────────────────────────
# HELPER: SAFE SNR CALCULATION
# ──────────────────────────────────────────────────────────────
def safe_snr(val, err):
    try:
        if err is None or pd.isna(err) or err <= 0:
            return 0
        if val is None or pd.isna(val):
            return 0
        return abs(val) / err
    except Exception:
        return 0

# ──────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────
for idx, row in df.iterrows():
    src_id = row['source_id']
    ra, dec = row['ra'], row['dec']
    print(f"[{current}/{total}] {src_id} | ", end="", flush=True)
    current += 1

    score = 0
    notes = []
    gaia_snr = "N/A"
    dsc_probs = "N/A"
    ps1_ext = "N/A"
    ps1_color = "N/A"
    tier = "UNKNOWN"

    # 1. GAIA: ASTROMETRY + DSC CLASSIFIER (Combined query)
    try:
        query = f"""
        SELECT 
            parallax, parallax_error, 
            pmra, pmra_error, pmdec, pmdec_error,
            classprob_dsc_combmod_star, 
            classprob_dsc_combmod_galaxy, 
            classprob_dsc_combmod_quasar
        FROM gaiadr3.gaia_source WHERE source_id = {src_id}
        """
        job = Gaia.launch_job(query)
        res = job.get_results()
        
        if len(res) > 0:
            g = res[0]
            
            # Astrometry
            plx_snr = safe_snr(g['parallax'], g['parallax_error'])
            pm_snr = max(safe_snr(g['pmra'], g['pmra_error']), safe_snr(g['pmdec'], g['pmdec_error']))
            gaia_snr = f"P={plx_snr:.1f}, PM={pm_snr:.1f}"
            
            if plx_snr < 3 and pm_snr < 3:
                score += 2; notes.append("Gaia: Extragalactic astrometry")
            elif plx_snr > 5 or pm_snr > 5:
                score -= 2; notes.append("Gaia: Stellar motion/parallax")
            
            # DSC Classifier
            star_prob = g.get('classprob_dsc_combmod_star', 0) or 0
            galaxy_prob = g.get('classprob_dsc_combmod_galaxy', 0) or 0
            
            if galaxy_prob > 0.9:
                score += 3; notes.append(f"Gaia ML: Strong Galaxy ({galaxy_prob:.2f})")
            elif star_prob > 0.9:
                score -= 3; notes.append(f"Gaia ML: Strong Star ({star_prob:.2f})")
                
            dsc_probs = f"Gal={galaxy_prob:.2f}"
        else:
            notes.append("Gaia: No data")
            
    except Exception:
        notes.append("Gaia: Query failed")

    time.sleep(1.5)  # Rate limit

    # 2. PAN-STARRS MORPHOLOGY (With Spatial Sorting)
    try:
        url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
        params = {"ra": ra, "dec": dec, "radius": 0.002} # Increased radius to 7.2"
        r = requests.get(url, params=params, timeout=10)
        
        if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
            lines = [l for l in r.text.split('\n') if not l.startswith('#')]
            if lines:
                ps1 = pd.read_csv(io.StringIO('\n'.join(lines)))
                if len(ps1) > 0:
                    # Sort by distance to target
                    if 'raMean' in ps1.columns and 'decMean' in ps1.columns:
                        ps1['sep2'] = (ps1['raMean'] - ra)**2 + (ps1['decMean'] - dec)**2
                        ps1 = ps1.sort_values('sep2')
                    
                    p = ps1.iloc[0]
                    
                    cols = ['gMeanPSFMag', 'gMeanKronMag', 'rMeanPSFMag', 'rMeanKronMag']
                    if all(c in ps1.columns for c in cols):
                        g_ext = p['gMeanPSFMag'] - p['gMeanKronMag']
                        r_ext = p['rMeanPSFMag'] - p['rMeanKronMag']
                        max_ext = max(g_ext, r_ext)
                        gr_color = p['gMeanPSFMag'] - p['rMeanPSFMag']
                        
                        ps1_ext = f"Δ={max_ext:.2f}"
                        ps1_color = f"g-r={gr_color:.2f}"

                        # Tiered Scoring for Extension
                        if max_ext > 0.8:
                            score += 3; notes.append(f"PS1: Strongly Extended (Δ={max_ext:.2f})")
                        elif max_ext > 0.5:
                            score += 2; notes.append(f"PS1: Extended (Δ={max_ext:.2f})")
                        elif max_ext < 0.1:
                            score -= 2; notes.append("PS1: Point source")

                        if gr_color < 0.5:
                            score += 1; notes.append("PS1: Blue color")
                    else:
                        notes.append("PS1: Missing magnitudes")
            else:
                notes.append("PS1: No match")
    except Exception:
        notes.append("PS1: API error")

    time.sleep(1.5)

    # Final Tier Assignment
    if score >= 5: tier = "T1_STRONG_GALAXY"
    elif score >= 3: tier = "T2_PROBABLE_GALAXY"
    elif score >= 0: tier = "T3_AMBIGUOUS"
    else: tier = "T0_REJECTED"

    results.append({
        'source_id': src_id, 'ra': ra, 'dec': dec,
        'gaia_astrometry_snr': gaia_snr, 'dsc_probs': dsc_probs,
        'ps1_extension': ps1_ext, 'ps1_color': ps1_color, 
        'priority_score': score, 'tier': tier,
        'diagnostic_notes': '; '.join(notes),
        'ps1_viewer_link': f"https://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos={ra}+{dec}&radius=10&width=3&height=3&color=color&imageType=stack&size=512",
        'legacy_viewer_link': f"https://legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&pixscale=0.262&bands=grz"
    })

    # Checkpoint
    pd.DataFrame(results).to_pickle(CHECKPOINT_FILE)
    print(f"✅ Score: {score} | Tier: {tier}")

# ──────────────────────────────────────────────────────────────
# FINALIZE
# ──────────────────────────────────────────────────────────────
out_df = pd.DataFrame(results)
out_df['rank'] = out_df['priority_score'].rank(method='min', ascending=False).astype(int)
out_df = out_df.sort_values('priority_score', ascending=False)

out_df.to_csv(OUTPUT_FILE, index=False)
if os.path.exists(CHECKPOINT_FILE):
    os.remove(CHECKPOINT_FILE)

print("\n" + "="*60)
print("✅ BATCH COMPLETE")
print(f"📁 Full results: {OUTPUT_FILE}")
print("\n🏆 TOP TIER-1 CANDIDATES:")
t1 = out_df[out_df['tier'] == 'T1_STRONG_GALAXY']
if len(t1) > 0:
    print(t1[['rank','source_id','priority_score','tier','ps1_extension','dsc_probs','diagnostic_notes']].to_string(index=False))
else:
    print("   None. Highest tier found: T2 or lower.")