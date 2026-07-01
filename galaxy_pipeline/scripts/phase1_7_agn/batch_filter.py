import pandas as pd
from astroquery.simbad import Simbad
from astroquery.ipac.ned import Ned
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

df = pd.read_csv("tight_candidates.csv")
results = []

print(f"🔍 Processing {len(df)} candidates...\n")

for idx, row in df.iterrows():
    print(f"[{idx+1}/{len(df)}] source_id={int(row['source_id'])} | RA={row['ra']:.4f} | DEC={row['dec']:.4f}")
    coord = SkyCoord(ra=row['ra']*u.deg, dec=row['dec']*u.deg)

    # Tier 1: SIMBAD @ 5"
    simbad_match = False
    try:
        sim = Simbad.query_region(coord, radius="5s")
        if sim is not None and len(sim) > 0:
            simbad_match = True
    except Exception:
        pass

    # Tier 2: NED @ 10"
    ned_match = False
    try:
        ned = Ned.query_region(coord, radius=10*u.arcsec)
        if ned is not None and len(ned) > 0:
            # Check if any match is extragalactic
            for _, r in ned.iterrows():
                obj_type = str(r.get('Object Type', '')).lower()
                if any(kw in obj_type for kw in ['galaxy', 'agn', 'qso', 'seyfert', 'comp']):
                    ned_match = True
                    break
    except Exception:
        pass

    # Priority Score Calculation
    base = row['classprob_dsc_combmod_galaxy'] - row['classprob_dsc_combmod_star'] - row['classprob_dsc_combmod_quasar']
    bonuses = (0 if simbad_match else 1) + (0 if ned_match else 1)
    final_score = base + bonuses

    results.append({
        'source_id': int(row['source_id']),
        'ra': row['ra'],
        'dec': row['dec'],
        'galaxy_prob': row['classprob_dsc_combmod_galaxy'],
        'simbad_match': simbad_match,
        'ned_match': ned_match,
        'score': final_score,
        'status': 'SURVIVOR' if (not simbad_match and not ned_match) else 'REJECTED'
    })
    time.sleep(2)  # Respect API rate limits

# Save full results
out_df = pd.DataFrame(results)
out_df.to_csv("batch_results.csv", index=False)

# Extract & sort survivors
survivors = out_df[out_df['status'] == 'SURVIVOR'].sort_values('score', ascending=False)
survivors.to_csv("survivors.csv", index=False)

print("\n✅ BATCH COMPLETE")
print(f"Total candidates: {len(df)}")
print(f"Survivors (not in SIMBAD/NED): {len(survivors)}")
print(f"\n TOP SURVIVORS:")
print(survivors.head(10).to_string(index=False))