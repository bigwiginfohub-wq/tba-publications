candidates = [
    {"id": 6158874323829427200, "ra": 192.109396, "dec": -34.116281},
    {"id": 4921284891965816832, "ra": 14.493363, "dec": -53.200202}
]

print("📸 MULTI-SURVEY CUTOUT LINKS\n" + "="*60)
for c in candidates:
    ra, dec = c['ra'], c['dec']
    print(f"\n🆔 {c['id']}")
    print(f"   Pan-STARRS DR2: https://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos={ra}+{dec}&radius=25&width=5&height=5&color=color&imageType=stack&size=600")
    print(f"   DESI Legacy DR10: https://legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&pixscale=0.262&bands=grz")
    print(f"   WISE AllWISE:     https://irsa.ipac.caltech.edu/ibe/image/wise/allwise/4b1/{ra}/{dec}/")
    print(f"   Aladin Interactive: http://aladin.u-strasbg.fr/AladinInteractive/?target={ra}+{dec}&radius=60&coodisp=J2000&layer=P%2FP")