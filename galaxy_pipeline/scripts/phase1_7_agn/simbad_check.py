from astroquery.simbad import Simbad

result = Simbad.query_object("Gaia DR3 141419666601293056")

print(result)