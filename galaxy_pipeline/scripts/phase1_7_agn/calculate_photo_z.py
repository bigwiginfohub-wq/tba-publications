import numpy as np
import matplotlib.pyplot as plt
import eazy

# 1. Convert your Pan-STARRS1 Kron magnitudes to flux density (uJy)
# Formula: Flux = 10**((23.9 - mag) / 2.5)
mags = np.array([18.229, 18.026, 18.034, 18.010, 17.926])
errs = np.array([0.02, 0.02, 0.02, 0.03, 0.04])

flux = 10**((23.9 - mags) / 2.5)
# Propagate magnitude errors to flux errors
flux_errs = flux * (errs * (np.log(10) / 2.5))

# 2. Define the Pan-STARRS1 filter mapping
# EAZY system profile IDs for PS1 g, r, i, z, y
filters = ['ps1.g', 'ps1.r', 'ps1.i', 'ps1.z', 'ps1.y']

print("--- EXTRAGALACTIC TARGET FLUX CONVERSION ---")
for f, fl, fe in zip(filters, flux, flux_errs):
    print(f"{f}: {fl:.2f} ± {fe:.2f} uJy")

# 3. Initialize local template fitting parameters
params = {}
params['CATALOG_FILE'] = 'placeholder'
params['Z_MAX'] = 4.0
params['Z_STEP'] = 0.01

# Running template matching
# (Mimics clicking the 'Run EAZY' button on the Leiden UI)
ez = eazy.photoz.PhotoZ(param_file=None, params=params, load_products=False)
# Fit the linear template combinations across the standard blue-starburst grid
