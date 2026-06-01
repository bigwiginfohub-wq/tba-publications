\# Pipeline Methodology v3.1



\## 1. Initial Selection

Sources extracted from Gaia DR3 using DSC classifier thresholds:

\- `classprob\_dsc\_combmod\_galaxy > 0.99`

\- `classprob\_dsc\_combmod\_star < 1e-8`



\## 2. Astrometric Filtering

Parallax and proper motion signal-to-noise ratios calculated as:

`SNR = |value| / error`

\- `SNR < 3.0` → Extragalactic distance (+2 pts)

\- `SNR > 5.0` → Likely stellar contaminant (-2 pts)

NaN/zero uncertainties handled via safe division.



\## 3. Morphological Scoring (Pan-STARRS DR2)

Spatial cross-match within 3.6" using nearest-neighbor sorting.

Extension metric: `Δ = PSF\_Mag − Kron\_Mag`

\- `Δ > 0.8` → Strongly extended (+3 pts)

\- `0.5 < Δ ≤ 0.8` → Extended (+2 pts)

\- `Δ < 0.1` → Point source (-2 pts)



\## 4. Color Selection

`g−r` color calculated from PSF magnitudes:

\- `g−r < 0.5` → Blue/star-forming (+1 pt)

\- `g−r > 1.3` → Red/stellar bias (-1 pt)



\## 5. Tier Assignment \& Ranking

| Score Range | Tier               | Interpretation                  |

|-------------|--------------------|---------------------------------|

| ≥ 6         | T1\_STRONG\_GALAXY   | Bright, resolved, high-confidence |

| 4–5         | T2\_PROBABLE\_GALAXY | Faint/compact, likely BCD/starburst |

| 0–3         | T3\_AMBIGUOUS       | Uncertain morphology or color   |

| < 0         | T0\_REJECTED        | Stellar or failed validation    |



Ranking uses stable sort: `priority\_score → ps1\_extension → galaxy\_prob`.



\## Selection Function \& Limitations

\- \*\*Optimized for:\*\* Blue star-forming galaxies, compact dwarfs, morphologically extended systems.

\- \*\*Down-weights:\*\* Red ellipticals, compact quasars, high-z unresolved galaxies, passive populations.

\- \*\*Catalog Gaps:\*\* Sources near `r ≈ 18–20` frequently lack spectroscopic/photo-z coverage due to historical targeting cuts.

\- \*\*Astrometry:\*\* Gaia DR3 archive instability handled via 3-attempt retry logic with exponential backoff.

