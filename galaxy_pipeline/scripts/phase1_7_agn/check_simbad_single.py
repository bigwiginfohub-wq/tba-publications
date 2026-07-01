from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u

coord = SkyCoord(
    ra=183.232798*u.deg,
    dec=53.460458*u.deg
)

result = Simbad.query_region(
    coord,
    radius='5s'
)

print(result)

     