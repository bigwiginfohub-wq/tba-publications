import pandas as pd
import numpy as np

print("="*60)
print("FINAL FORENSICS: 4 CONFIRMED vs. 12 PURE UNKNOWNS")
print("="*60)

# 1. Load the full audit and the NED results
df = pd.read_csv('crossmatch_audit_new_candidates.csv')
ned = pd.read_csv('phase3_ned_strict.csv')

# 2. Identify the 5 NED stars to exclude them
ned_matches = ned[ned['ned_found'] == True]['source_id'].tolist()
print(f"\nExcluding {len(ned_matches)} NED-identified stellar contaminants.")

# 3. Split into Confirmed and Pure Unknowns
confirmed = df[df['label_confidence_tier'] == 'Tier_1_Extragalactic_High'].copy()
pure_unknowns = df[(df['label_confidence_tier'] == 'Tier_0_Unknown') & (~df['source_id'].isin(ned_matches))].copy()

print(f"Remaining Pure Unknowns: {len(pure_unknowns)}")

# 4. Calculate the critical physical metrics
for subset in [confirmed, pure_unknowns]:
    # Parallax Signal-to-Noise Ratio (Near 0 means distant/stationary)
    subset['parallax_snr'] = np.abs(subset['parallax'] / subset['parallax_error'])
    # Total Proper Motion (Near 0 means distant/stationary)
    subset['pm_total'] = np.sqrt(subset['pmra']**2 + subset['pmdec']**2)

cols = ['parallax_snr', 'pm_total', 'ruwe']

print("\n--- 4 CONFIRMED EXTRAGALACTIC (The Benchmark) ---")
print(confirmed[cols].describe())

print("\n--- 12 PURE UNKNOWNS (Absent from SIMBAD & NED) ---")
print(pure_unknowns[cols].describe())

print("\n" + "="*60)
print("INTERPRETATION GUIDE:")
print("If Pure Unknowns have parallax_snr < 2.0 and pm_total < 1.0,")
print("they are physically consistent with distant, stationary objects.")
print("="*60)