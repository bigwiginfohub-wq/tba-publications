import numpy as np
import scipy.stats as stats

print("--- EXTRAGALACTIC SED TEMPLATE FITTER ---")

# 1. Your converted Pan-STARRS1 fluxes (uJy) and errors
wavelengths = np.array([4810, 6170, 7520, 8660, 9620]) # g, r, i, z, y effective wavelengths in Angstroms
flux_obs = np.array([185.52, 223.67, 222.02, 226.99, 245.24])
flux_err = np.array([3.42, 4.12, 4.09, 6.27, 9.04])

# 2. Generate a grid of redshifts to test (from z = 0.0 to 1.5)
z_grid = np.arange(0.0, 1.5, 0.005)
chi2_list = []

# 3. Simple Blue Compact/Starburst synthetic template template 
# (Flat in frequency f_nu, with a strong simulated OIII/H-alpha line complex)
def get_template_flux(z):
    # Shift rest-frame features into observed frame
    base_sed = np.ones_like(wavelengths) * 210.0
    # Add an emission line bump that travels through bands based on redshift
    h_alpha_obs = 6563 * (1 + z)
    o3_obs = 5007 * (1 + z)
    
    # Simple Gaussian mapping for emission lines landing in filters
    bump = 35 * np.exp(-((wavelengths - h_alpha_obs)/500)**2) + 40 * np.exp(-((wavelengths - o3_obs)/400)**2)
    return base_sed + bump

# 4. Perform the Chi-Square Minimization Loop
for z in z_grid:
    flux_model = get_template_flux(z)
    # Calculate scale factor (normalization constant 'scale')
    scale = np.sum((flux_obs * flux_model) / flux_err**2) / np.sum(flux_model**2 / flux_err**2)
    # Calculate Chi2
    chi2 = np.sum(((flux_obs - scale * flux_model) / flux_err) ** 2)
    chi2_list = np.array(chi2)
    chi2_list = np.append(chi2_list, chi2) # fix list syntax below

# Re-array correctly
chi2_list = []
for z in z_grid:
    flux_model = get_template_flux(z)
    scale = np.sum((flux_obs * flux_model) / flux_err**2) / np.sum(flux_model**2 / flux_err**2)
    chi2 = np.sum(((flux_obs - scale * flux_model) / flux_err) ** 2)
    chi2_list.append(chi2)

chi2_list = np.array(chi2_list)

# 5. Extract target variables
best_idx = np.argmin(chi2_list)
z_best = z_grid[best_idx]
min_chi2 = chi2_list[best_idx]

# Convert chi2 to a probability density function (PDF)
likelihood = np.exp(-0.5 * (chi2_list - min_chi2))
pdf = likelihood / np.sum(likelihood)

# Calculate 68% Confidence Interval (z_err)
cumulative_pdf = np.cumsum(pdf)
z_low = z_grid[np.searchsorted(cumulative_pdf, 0.16)]
z_high = z_grid[np.searchsorted(cumulative_pdf, 0.84)]
z_err = (z_high - z_low) / 2.0

print("==========================================")
print(f" RESULTS FOR COMPACT CANDIDATE")
print("==========================================")
print(f" z_best (Peak Redshift) : {z_best:.3f}")
print(f" z_err (68% Confidence) : ± {z_err:.3f}")
print(f" chi2 (Fit Quality)     : {min_chi2:.2f}")
print("------------------------------------------")

# Check fit health
if min_chi2 < 2.0:
    print(" Verdict: Excellent template match.")
elif min_chi2 > 5.0:
    print(" Verdict: Template mismatch warning.")

# Simple ASCII check for Bimodality / Double Peaks
peaks = [z_grid[i] for i in range(1, len(pdf)-1) if pdf[i] > pdf[i-1] and pdf[i] > pdf[i+1] and pdf[i] > 0.05]
if len(peaks) > 1:
    print(f"⚠️ BIMODALITY DETECTED: Secondary solution found at z = {peaks[1]:.2f}")
