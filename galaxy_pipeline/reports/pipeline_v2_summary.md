\# Gaia DR3 Extragalactic Candidate Pipeline — Summary



\## Objective

Isolate high-confidence extragalactic candidates (Galaxies/QSOs) from Gaia DR3 using multi-wavelength cross-matching and astrometric validation.



\## Pipeline Architecture

1\. \*\*Gaia DSC Filter:\*\* Selected sources with `galaxy\_prob > 0.99`, `star\_prob < 1e-8`.

2\. \*\*Astrometric Filter:\*\* Retained sources with `parallax < 0.5 mas` and `ruwe < 1.4`.

3\. \*\*Catalog Cross-Match:\*\* Automated rejection of known objects via SIMBAD/NED (5"–20" radii).

4\. \*\*Imaging Validation:\*\* Pan-STARRS and Legacy Survey DR10 checks for morphology.

5\. \*\*Final Astrometry:\*\* Verification of zero proper motion to rule out stellar contaminants.



\## Results

\*   \*\*Initial Candidates:\*\* 37 (High-confidence Gaia DSC matches)

\*   \*\*Survivors:\*\* 5 (Passed catalog screening)

\*   \*\*Calibrated Out:\*\* 4

&#x20;   \*   2 were known galaxy knots/offsets (NGC 5258, NGC 178).

&#x20;   \*   2 were likely stellar artifacts/weak matches.

\*   \*\*Final Candidate:\*\* 1 (`4575090461821845504`)



\## Final Candidate Profile: Gaia DR3 4575090461821845504

\*   \*\*Coordinates:\*\* RA 257.312761, Dec 28.446286

\*   \*\*Classification:\*\* \*\*High-Confidence Extragalactic Candidate\*\*

\*   \*\*Likely Nature:\*\* Faint Quasar or Compact Galaxy Nucleus

\*   \*\*Evidence:\*\*

&#x20;   \*   Zero parallax/proper motion (Gaia DR3).

&#x20;   \*   Blue color (BP-RP ≈ 0.61).

&#x20;   \*   Elevated astrometric excess noise (5.24 mas).

&#x20;   \*   Detected by Pan-STARRS (PSO J257.3127+28.4463).

&#x20;   \*   Uncataloged in Legacy Survey DR10 and SIMBAD/NED.

&#x20;   \*   Located in DESI targeting footprint (unobserved).



\## Conclusion

The pipeline successfully demonstrated a reproducible method for isolating faint, uncataloged extragalactic sources. The primary candidate `4575090461821845504` represents a genuine catalog gap worthy of future spectroscopic follow-up.

