import pandas as pd

print("Loading 12,500 random sky sources...")
df = pd.read_csv('gaia_phase1_scaled_10k.csv')

# 1. Photometric cuts (Brightness, Color, Astrometric Fit)
c_g = (df['phot_g_mean_mag'] >= 18.0) & (df['phot_g_mean_mag'] <= 21.1)
c_bp_rp = (df['bp_rp'] >= 0.50) & (df['bp_rp'] <= 0.70)
c_ruwe = (df['ruwe'] >= 0.88) & (df['ruwe'] <= 1.40)

# 2. Astrometric cuts (The "Zero Motion" Extragalactic Filter)
c_plx = df['parallax'].abs() <= 0.5
c_pmra = df['pmra'].abs() <= 1.0
c_pmdec = df['pmdec'].abs() <= 1.0

# Apply all 6 cuts
final_candidates = df[c_g & c_bp_rp & c_ruwe & c_plx & c_pmra & c_pmdec]

print(f"✅ SUCCESS! Extracted {len(final_candidates)} final, purified candidates.")
final_candidates.to_csv('gaia_phase1_final_candidates.csv', index=False)