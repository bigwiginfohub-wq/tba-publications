from astroquery.gaia import Gaia
import time

ra, dec = 257.312761, 28.446286
radius_deg = 0.0003  # ~1.1 arcseconds

query = f"""
SELECT TOP 1
    source_id,
    parallax,
    parallax_error,
    pmra,
    pmra_error,
    pmdec,
    pmdec_error,
    phot_g_mean_mag,
    bp_rp,
    ruwe,
    astrometric_excess_noise
FROM gaiadr3.gaia_source
WHERE CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
) = 1
"""

print(" Querying Gaia DR3 by coordinates (bypasses source_id instability)...")
print("⏳ May take 10-30s. Retrying up to 3 times if archive is busy.\n")

for attempt in range(3):
    try:
        job = Gaia.launch_job(query)
        res = job.get_results()
        if len(res) > 0:
            break
        print(f"  Attempt {attempt+1}: Empty result. Retrying...")
        time.sleep(5)
    except Exception as e:
        print(f"  Attempt {attempt+1}: {e}. Retrying...")
        time.sleep(5)
else:
    print("❌ Archive failed to return data after 3 attempts. Wait 2 mins and retry.")
    exit()

# --- Process Result ---
row = res[0]
print("✅ GAIA DR3 ASTROMETRY RETRIEVED")
print("="*50)
print(f"Source ID:       {row['source_id']}")
print(f"G Mag:           {row['phot_g_mean_mag']:.3f}")
print(f"BP-RP Color:     {row['bp_rp']:.3f}")
print(f"RUWE:            {row['ruwe']:.3f}")
print(f"Excess Noise:    {row['astrometric_excess_noise']:.4f}")
print("-" * 30)
print("ASTROMETRIC DATA:")
print(f"Parallax:        {row['parallax']:.4f} +/- {row['parallax_error']:.4f} mas")
print(f"PM RA:           {row['pmra']:.4f} +/- {row['pmra_error']:.4f} mas/yr")
print(f"PM Dec:          {row['pmdec']:.4f} +/- {row['pmdec_error']:.4f} mas/yr")

# --- Decisive Test ---
print("\n" + "="*50)
print("🧪 INTERPRETATION:")

plx_snr = abs(row['parallax']) / row['parallax_error'] if row['parallax_error'] > 0 else 0
pm_snr = max(
    abs(row['pmra']) / row['pmra_error'] if row['pmra_error'] > 0 else 0,
    abs(row['pmdec']) / row['pmdec_error'] if row['pmdec_error'] > 0 else 0
)

if plx_snr < 3.0 and pm_snr < 3.0:
    print("✅ VERDICT: EXTRAGALACTIC (Quasar / Distant Galaxy)")
    print("   -> Parallax & Proper Motion are statistically consistent with zero.")
    print("   -> Object is at cosmological distance. Matches Pan-STARRS detection.")
else:
    print("❌ VERDICT: STELLAR (Milky Way Star)")
    print(f"   -> Significant motion detected (Parallax SNR: {plx_snr:.1f} | PM SNR: {pm_snr:.1f})")
    print("   -> Classifier false positive. Discard from extragalactic list.")