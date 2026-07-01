import requests
import pandas as pd
import io

ra, dec = 257.312761, 28.446286
print("🔍 MULTI-SURVEY MORPHOLOGY & EXTENSION CHECK\n" + "="*55)

# ──────────────────────────────────────────────────────────────
# 1. PAN-STARRS DR2: PSF vs Kron Magnitudes
# ──────────────────────────────────────────────────────────────
ps1_url = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv"
ps1_params = {"ra": ra, "dec": dec, "radius": 0.001}  # ~3.6 arcsec
r = requests.get(ps1_url, params=ps1_params, timeout=10)

print("\n📡 PAN-STARRS DR2 EXTENSION CHECK:")
if r.ok and r.text.strip() and not r.text.startswith("<!DOCTYPE"):
    lines = [l for l in r.text.split('\n') if not l.startswith('#')]
    if lines:
        df = pd.read_csv(io.StringIO('\n'.join(lines)))
        if len(df) > 0:
            row = df.iloc[0]
            ext_flags = {}
            for band in ['g', 'r', 'i']:
                psf_col = f"{band}MeanPSFMag"
                kron_col = f"{band}MeanKronMag"
                if psf_col in df.columns and kron_col in df.columns:
                    psf = row[psf_col]
                    kron = row[kron_col]
                    ext = psf - kron
                    ext_flags[band] = ext
                    flag = "POINT" if ext < 0.05 else "EXTENDED" if ext > 0.2 else "MARGINAL"
                    print(f"  {band}-band: PSF={psf:.3f} | Kron={kron:.3f} | Δ={ext:.3f} ({flag})")
            if not ext_flags:
                print("  ⚠️ Kron magnitudes not available for this source.")
        else:
            print("  ️ No PS1 match within ~3.6\"")
    else:
        print("  ️ Empty PS1 response")
else:
    print("  ❌ PS1 API failed or returned HTML")

# ──────────────────────────────────────────────────────────────
# 2. LEGACY SURVEY DR10: Tractor Morphology Type
# ─────────────────────────────────────────────────────────────
print("\n📡 LEGACY SURVEY DR10 MORPHOLOGY CHECK:")
ls_url = f"https://legacysurvey.org/dr10/catalogs/search/?ra={ra}&dec={dec}&radius=0.001&rowlimit=5&format=csv"
try:
    r_ls = requests.get(ls_url, timeout=10)
    if r_ls.ok and r_ls.text.strip() and not r_ls.text.startswith("<!DOCTYPE"):
        lines_ls = [l for l in r_ls.text.split('\n') if not l.startswith('#')]
        if lines_ls:
            df_ls = pd.read_csv(io.StringIO('\n'.join(lines_ls)))
            if len(df_ls) > 0:
                row_ls = df_ls.iloc[0]
                ls_type = str(row_ls.get('type', 'UNKNOWN')).upper()
                ls_id = row_ls.get('ls_id', 'N/A')
                print(f"  ✅ LS_DR10 Match Found:")
                print(f"    LS_ID: {ls_id}")
                print(f"    TYPE:  {ls_type}")
                
                if ls_type in ['EXP', 'DEV', 'REX', 'SER', 'COMP']:
                    print("    👉 GALAXY morphology confirmed")
                elif ls_type == 'PSF':
                    print("    👉 Point source (consistent with QSO or star)")
                else:
                    print(f"    ⚠️ Unrecognized type: {ls_type}")
            else:
                print("  ⚠️ No LS_DR10 match within ~3.6\"")
        else:
            print("  ⚠️ Empty LS_DR10 response")
    else:
        print("  ⚠️ LS_DR10 API returned non-CSV (server-side issue). Rely on PS1 extension.")
except Exception as e:
    print(f"  ❌ LS_DR10 query failed: {str(e)[:40]}")

print("\n" + "="*55)
print("📝 QUICK INTERPRETATION GUIDE:")
print("  • Δ(PSF-Kron) > 0.2  → Strong galaxy extension")
print("  • LS TYPE = EXP/DEV/REX → Confirmed resolved galaxy")
print("  • LS TYPE = PSF + g-r < 0 → Likely QSO/AGN nucleus")
print("  • Mixed signals → Compact galaxy with active nucleus")