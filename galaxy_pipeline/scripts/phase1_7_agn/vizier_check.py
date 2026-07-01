from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

coord = SkyCoord(ra=204.992453*u.deg, dec=0.834006*u.deg)

print("Querying VizieR (NED + LEDA) within 15 arcseconds...\n")
viz = Vizier(columns=["_RAJ2000", "_DEJ2000", "Name", "Type", "Redshift"])
result = viz.query_region(coord, radius="15s", catalog=["VII/269/ned", "VII/237/leda"])

if not result:
    print("️ No VizieR/NED/LEDA matches.")
else:
    for cat_name, table in result.items():
        print(f"📂 {cat_name}:")
        print(table[["Name", "Type", "Redshift"]])
        print()