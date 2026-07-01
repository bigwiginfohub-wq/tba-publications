from astroquery.ipac.ned import Ned
from astropy.coordinates import SkyCoord
import astropy.units as u
import time

candidates = [
    (192.109396, -34.116281),  # Rank 1
    (257.312761,  28.446286),  # Rank 2
    (204.992453,   0.834006)   # Rank 3
]

print("NED Cross-Match (1 arcsecond radius)\n" + "="*50)

for i, (ra, dec) in enumerate(candidates, 1):
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    print(f"\n[Rank {i}] RA={ra} | DEC={dec}")

    try:
        result = Ned.query_region(coord, radius=1*u.arcsec)

        if result is None or len(result) == 0:
            print("STATUS: NOT FOUND in NED → Tier-1 Candidate")
        else:
            print(f"STATUS: FOUND in NED ({len(result)} match(es))")
            # Safely print all returned columns without guessing names
            for col in result.colnames:
                print(f"  {col}: {result[col][0]}")

    except Exception as e:
        print(f"  ERROR: {e}")

    time.sleep(2)  # Prevent NED rate-limiting