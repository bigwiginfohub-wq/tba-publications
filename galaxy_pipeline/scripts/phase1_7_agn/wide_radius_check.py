from astroquery.simbad import Simbad
from astroquery.ipac.ned import Ned
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

coord = SkyCoord(ra=9.785671*u.deg, dec=-14.174743*u.deg)
radii = [15, 30, 60]

print("🔍 WIDE-RADIUS CATALOG SEARCH FOR 2374402820540535808\n" + "="*60)
for rad in radii:
    print(f"\n📏 RADIUS: {rad}\"")
    print("-" * 40)

    # SIMBAD
    try:
        sim = Simbad.query_region(coord, radius=f"{rad}s")
        if sim is not None and len(sim) > 0:
            col = next((c for c in sim.colnames if c.lower() == 'main_id'), sim.colnames[0])
            print(f"SIMBAD: {sim[col][0]}")
        else:
            print("SIMBAD: NONE")
    except Exception as e:
        print(f"SIMBAD: ERROR")

    # NED
    try:
        ned = Ned.query_region(coord, radius=rad*u.arcsec)
        if ned is not None and len(ned) > 0:
            print(f"NED:    {len(ned)} match(es)")
            if 'Object Name' in ned.colnames and 'Object Type' in ned.colnames:
                for i in range(min(2, len(ned))):
                    print(f"        {ned['Object Name'][i]} | {ned['Object Type'][i]}")
        else:
            print("NED:    NONE")
    except Exception:
        print(f"NED:    TIMEOUT")

    # VizieR (NED + LEDA + SDSS Galaxies)
    try:
        viz = Vizier(columns=["Name", "Type"])
        v_res = viz.query_region(coord, radius=f"{rad}s", catalog=["VII/269/ned", "VII/237/leda", "V/147/sdss12"])
        matches = [t["Name"][0] for t in v_res.values() if len(t) > 0]
        print(f"VizieR: {', '.join(matches[:3]) if matches else 'NONE'}")
    except Exception:
        print(f"VizieR: ERROR")

    time.sleep(2)  # Respect API rate limits