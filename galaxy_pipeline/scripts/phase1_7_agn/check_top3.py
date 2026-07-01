from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u

candidates = [
    (192.109396, -34.116281),  # Rank 1
    (257.312761,  28.446286),  # Rank 2
    (204.992453,   0.834006)   # Rank 3
]

print("Tight SIMBAD Cross-Match (1 arcsecond radius)\n" + "="*50)

for i, (ra, dec) in enumerate(candidates, 1):
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    result = Simbad.query_region(coord, radius="1s")
    
    print(f"\n[Rank {i}] RA={ra} | DEC={dec}")
    if result is None or len(result) == 0:
        print("STATUS: NOT FOUND in SIMBAD (1\" radius)")
    else:
        print("MATCHED:", result["MAIN_ID"][0])