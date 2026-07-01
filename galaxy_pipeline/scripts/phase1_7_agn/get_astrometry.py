from astroquery.gaia import Gaia

source_id = 4575090461821845504

query = f"""
SELECT
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
WHERE source_id = {source_id}
"""

print("🔍 RETRIEVING ASTROMETRY FOR SOURCE:", source_id)
print("="*50)

try:
    job = Gaia.launch_job(query)
    res = job.get_results()

    if len(res) == 0:
        print("⚠️ No data found.")
    else:
        row = res[0]
        
        # Print raw values
        print(f"Source ID:       {row['source_id']}")
        print(f"Magnitude (G):   {row['phot_g_mean_mag']:.3f}")
        print(f"Color (BP-RP):   {row['bp_rp']:.3f}")
        print(f"RUWE:            {row['ruwe']:.3f}")
        print("-" * 30)
        print("ASTROMETRIC DATA:")
        print(f"Parallax:        {row['parallax']:.4f} +/- {row['parallax_error']:.4f} mas")
        print(f"Proper Motion RA: {row['pmra']:.4f} +/- {row['pmra_error']:.4f} mas/yr")
        print(f"Proper Motion Dec:{row['pmdec']:.4f} +/- {row['pmdec_error']:.4f} mas/yr")
        print(f"Excess Noise:    {row['astrometric_excess_noise']:.4f}")

        # --- THE DECISIVE TEST ---
        print("\n" + "="*50)
        print(" INTERPRETATION:")

        # Check Parallax Significance
        parallax_snr = abs(row['parallax']) / row['parallax_error'] if row['parallax_error'] > 0 else 0
        
        # Check Proper Motion Significance
        pm_ra_snr = abs(row['pmra']) / row['pmra_error'] if row['pmra_error'] > 0 else 0
        pm_dec_snr = abs(row['pmdec']) / row['pmdec_error'] if row['pmdec_error'] > 0 else 0
        pm_total_snr = max(pm_ra_snr, pm_dec_snr)

        if parallax_snr < 3.0 and pm_total_snr < 3.0:
            print("✅ VERDICT: EXTRAGALACTIC (Quasar or Galaxy)")
            print("   -> No significant movement detected. Likely distant background object.")
        else:
            print("❌ VERDICT: STELLAR (Star in Milky Way)")
            print("   -> Significant parallax or motion detected (>3-sigma).")
            
except Exception as e:
    print(f"❌ Error: {e}")