from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
import astropy.units as u

coord = SkyCoord(ra=204.99245343657478*u.deg, dec=0.8340056183165048*u.deg)
print("Querying SDSS DR16 (12 arcsec)...\n")

try:
    result = SDSS.query_region(
        coord,
        radius=12*u.arcsec,
        data_release=16,
        photoobj_fields=['objid', 'ra', 'dec', 'type', 'clean', 'g', 'r', 'i', 'z', 'probPSF']
    )
    if result is None or len(result) == 0:
        print("️ No SDSS match within 12\".")
    else:
        print("✅ SDSS MATCH:")
        print(result)
        print(f"\nType (3=Galaxy): {result['type'][0]}")
        print(f"probPSF (low=extended): {result['probPSF'][0]:.4f}")
except Exception as e:
    print(f"❌ SDSS Error: {e}")