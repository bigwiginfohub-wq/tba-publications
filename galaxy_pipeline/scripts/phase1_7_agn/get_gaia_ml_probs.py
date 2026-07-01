from astroquery.gaia import Gaia
import time

# ID from your latest message (verify it matches RA/Dec if needed)
source_id = 4575090461821845760

query = f"""
SELECT 
    source_id,
    classprob_dsc_combmod_quasar,
    classprob_dsc_combmod_galaxy, 
    classprob_dsc_combmod_star,
    classprob_dsc_combmod_planet,
    classprob_dsc_combmod_solar_system
FROM gaiadr3.gaia_source
WHERE source_id = {source_id}
"""

print("🔍 Querying Gaia DR3 ML Classification Probabilities...\n")
for attempt in range(3):
    try:
        job = Gaia.launch_job(query)
        res = job.get_results()
        if len(res) > 0:
            break
        print(f"  Attempt {attempt+1}: Empty. Retrying...")
        time.sleep(5)
    except Exception as e:
        print(f"  Attempt {attempt+1}: {e}. Retrying...")
        time.sleep(5)
else:
    print("❌ Failed to retrieve data after 3 attempts.")
    exit()

row = res[0]
print("✅ GAIA DR3 ML CLASSIFICATION:")
print(f"  Quasar:  {row['classprob_dsc_combmod_quasar']:.6f}")
print(f"  Galaxy:  {row['classprob_dsc_combmod_galaxy']:.6f}")
print(f"  Star:    {row['classprob_dsc_combmod_star']:.6f}")
print(f"  Planet:  {row['classprob_dsc_combmod_planet']:.6f}")
print(f"  SS Obj:  {row['classprob_dsc_combmod_solar_system']:.6f}")

# Interpretation
probs = {
    'Quasar': row['classprob_dsc_combmod_quasar'],
    'Galaxy': row['classprob_dsc_combmod_galaxy'],
    'Star': row['classprob_dsc_combmod_star']
}
top = max(probs, key=probs.get)
print(f"\n👉 GAIA'S TOP CLASSIFICATION: {top.upper()} (Prob: {probs[top]:.3f})")

print("\n📊 INTERPRETATION:")
if probs['Quasar'] > 0.7:
    print("  🔴 Strong ML support for QSO/AGN. Matches blue PS1 colors + zero motion.")
elif probs['Galaxy'] > 0.7:
    print("  🟩 Strong ML support for resolved galaxy. Matches extended morphology.")
elif probs['Quasar'] > 0.4 and probs['Galaxy'] > 0.4:
    print("  🟡 Split probability → Classic AGN host signature (compact nucleus + faint host).")
else:
    print("  ️ Low confidence across classes. May indicate faint/marginal source or classifier edge case.")