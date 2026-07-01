from astroquery.simbad import Simbad
from astroquery.ipac.ned import Ned
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

coord = SkyCoord(ra=204.99245343657478*u.deg, dec=0.8340056183165048*u.deg)

for rad in [15, 30]:
    print(f"\n🔍 SEARCHING AT {rad}\" RADIUS:")
    print("-" * 40)

    # SIMBAD (robust column lookup)
    sim = Simbad.query_region(coord, radius=f"{rad}s")
    if sim is not None and len(sim) > 0:
        col = next((c for c in sim.colnames if c.lower() == 'main_id'), sim.colnames[0])
        print(f"SIMBAD: {sim[col][0]}")
    else:
        print("SIMBAD: NONE")

    # NED
    try:
        ned = Ned.query_region(coord, radius=rad*u.arcsec)
        if ned is not None and len(ned) > 0:
            print(f"NED:    {len(ned)} match(es)")
            print(ned[['Object Name', 'Object Type']][:2])
        else:
            print("NED:    NONE")
    except Exception as e:
        print(f"NED:    TIMEOUT/ERROR ({e})")

    # VizieR (NED + LEDA)
    viz = Vizier(columns=["Name", "Type"])
    v_res = viz.query_region(coord, radius=f"{rad}s", catalog=["VII/269/ned", "VII/237/leda"])
    v_names = [t["Name"][0] for t in v_res.values() if len(t) > 0] if v_res else []
    print(f"VizieR: {', '.join(v_names) if v_names else 'NONE'}")

    time.sleep(2)  # Respect API rate limits