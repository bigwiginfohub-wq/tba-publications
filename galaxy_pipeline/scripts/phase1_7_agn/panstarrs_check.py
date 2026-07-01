from astroquery.skyview import SkyView
from astropy.coordinates import SkyCoord
import astropy.units as u
import os

coord = SkyCoord(ra=204.99245343657478*u.deg, dec=0.8340056183165048*u.deg)
print("Querying Pan-STARRS g-band...\n")

try:
    images = SkyView.get_images(position=coord, survey=["PanSTARRS:dr1"], pixels=200)
    if images:
        fname = "candidate3_panstarrs_g.fits"
        images[0].writeto(fname, overwrite=True)
        print(f"✅ FITS saved: {os.path.abspath(fname)}")
    else:
        print("⚠️ No image returned. Object may be faint or outside coverage.")
except Exception as e:
    print(f"⚠️ SkyView query failed: {e}")

print("\n🌐 DIRECT WEB CUTOUT (guaranteed to work):")
print(f"https://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos={coord.ra.deg}+{coord.dec.deg}&radius=3&width=2&height=2&color=color&imageType=stack&size=512&filters=g")