import pandas as pd

print("="*80)
print("PHASE 6: VISUAL TRIAGE & IMAGE INSPECTION LINKS")
print("="*80)

df = pd.read_csv('phase4_final_ranked_candidates.csv')

# Isolate the top 3 WISE AGN candidates
top3 = df.head(3).copy()

# Print the Reviewer's Summary Table
cols = ['source_id', 'ra', 'dec', 'w1_w2_color', 'parallax_snr', 'pm_total']
print("\n--- TOP 3 CANDIDATE SUMMARY ---")
print(top3[cols].to_string(index=False))

print("\n" + "="*80)
print("VISUAL INSPECTION LINKS (DESI Legacy Survey)")
print("Click these links to view the optical/infrared cutouts of your candidates.")
print("="*80)

for idx, row in top3.iterrows():
    ra = row['ra']
    dec = row['dec']
    sid = row['source_id']
    
    # Legacy Survey Sky Viewer URL (Deep optical + IR)
    legacy_url = f"https://www.legacysurvey.org/viewer?ra={ra:.6f}&dec={dec:.6f}&layer=ls-dr9&zoom=4&mark={ra:.6f},{dec:.6f}"
    
    # IRSA Finder Chart (WISE / 2MASS / Spitzer)
    irsa_url = f"https://irsa.ipac.caltech.edu/applications/finderchart/?ra={ra:.6f}&dec={dec:.6f}&size=2"
    
    print(f"\n🔭 SOURCE: {sid}")
    print(f"   Coords: RA {ra:.4f}, Dec {dec:.4f}")
    print(f"   1. Legacy Survey (Optical/Deep): {legacy_url}")
    print(f"   2. IRSA Finder (WISE Infrared):  {irsa_url}")

print("\n" + "="*80)
print("WHAT TO LOOK FOR IN THE IMAGES:")
print("- Fuzzy/Extended halo in Legacy? -> GALAXY")
print("- Sharp point source in Legacy + Bright in WISE? -> QUASAR (QSO)")
print("- Invisible in Legacy but bright in IRSA WISE? -> OBSCURED AGN")
print("- Multiple overlapping sources? -> BLENDING ARTIFACT")
print("="*80)