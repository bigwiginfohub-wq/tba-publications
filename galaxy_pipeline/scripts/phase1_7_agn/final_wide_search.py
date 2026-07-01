from astroquery.simbad import Simbad
from astroquery.ipac.ned import Ned
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

candidates = [
    {"id": 6158874323829427200, "ra": 192.109396, "dec": -34.116281},
    {"id": 4921284891965816832, "ra": 14.493363, "dec": -53.200202}
]

radii = [15, 30, 60, 120]

print("🔍 WIDE-RADIUS BATCH SEARCH (15\" → 120\")\n" + "="*60)
for cand in candidates:
    print(f"\n📡 TARGET: {cand['id']} | RA={cand['ra']:.4f} DEC={cand['dec']:.4f}")
    print("-" * 60)
    coord = SkyCoord(ra=cand['ra']*u.deg, dec=cand['dec']*u.deg)

    for rad in radii:
        print(f"  🔸 {rad}\" radius:")
        
        # SIMBAD
        try:
            sim = Simbad.query_region(coord, radius=f"{rad}s")
            if sim is not None and len(sim) > 0:
                col = next((c for c in sim.colnames if c.lower() == 'main_id'), sim.colnames[0])
                print(f"      SIMBAD: {sim[col][0]}")
            else:
                print(f"      SIMBAD: NONE")
        except Exception:
            print(f"      SIMBAD: ERROR")

        # NED
        try:
            ned = Ned.query_region(coord, radius=rad*u.arcsec)
            if ned is not None and len(ned) > 0:
                print(f"      NED:    {len(ned)} match(es)")
            else:
                print(f"      NED:    NONE")
        except Exception:
            print(f"      NED:    TIMEOUT")
            
        time.sleep(1.2)  # Respect API rate limits
    print()