\# TRACEBIND: Methodological Standards \& Frozen Metrics



This document defines the architectural boundaries, frozen mathematical definitions, and validation standards for the TRACEBIND framework. Any future modifications to these core metrics must be versioned (e.g., `v2.0`) and subjected to the same rigorous validation pipeline.



\---



\## 1. The Three Independent Engines

TRACEBIND is strictly divided into three independent scientific engines. \*\*Cross-contamination of metrics between engines is forbidden.\*\* There are no "unified super-scores."



\* \*\*Engine A: Extragalactic Reconciliation\*\*

&#x20; \* \*Purpose:\* Multi-survey cross-matching (Gaia, DESI, WISE, SIMBAD, NED) to isolate overlooked AGN/galaxy candidates.

&#x20; \* \*Core Metric:\* Morphological/Photometric Scoring.

\* \*\*Engine B: Kinematic Statistics\*\*

&#x20; \* \*Purpose:\* Mapping large-scale proper-motion structure and directional coherence in the Milky Way.

&#x20; \* \*Core Metric:\* Directional Coherence ($C\_f$).

\* \*\*Engine C: Astrometric Tension\*\*

&#x20; \* \*Purpose:\* Identifying stars where Gaia's single-star astrometric model fails, prioritizing unresolved companions.

&#x20; \* \*Core Metric:\* Astrometric Tension Score.



\---



\## 2. Frozen Metrics (v1.0)



\### Metric 1: Directional Coherence ($C\_f$ v1.0)

\* \*\*Engine:\*\* B (Kinematic Statistics)

\* \*\*Mathematical Definition:\*\* The Mean Resultant Length ($R$) of local proper-motion unit vectors.

&#x20; $$C\_f = \\sqrt{ \\left( \\frac{1}{N} \\sum u\_x \\right)^2 + \\left( \\frac{1}{N} \\sum u\_y \\right)^2 }$$

&#x20; where $u\_x = \\mu\_{\\alpha} / |\\mu|$ and $u\_y = \\mu\_{\\delta} / |\\mu|$.

\* \*\*Status:\*\* Analytically validated against circular statistics ($\\sigma \\approx \\sqrt{-2\\ln(C\_f)}$). Frozen.



\### Metric 2: Astrometric Tension Score (v1.0)

\* \*\*Engine:\*\* C (Astrometric Tension)

\* \*\*Mathematical Definition:\*\* The logarithmic composition of Gaia DR3 astrometric noise flags, designed to compress the heavy-tail of model failures.

&#x20; $$Tension = \\log\_{10}(\\max(RUWE, 0.1)) + \\log\_{10}(1 + \\max(Noise, 0))$$

\* \*\*Status:\*\* Validated against Gaia DR3 NSS catalogs (Odds Ratio 6.12, $p = 9.44 \\times 10^{-6}$). Proven to provide independent predictive power beyond raw RUWE/Noise (Logistic Pseudo-R² $\\Delta \\approx 0.15$). Frozen.



\---



\## 3. Validation Standards

No TRACEBIND metric or catalog may be claimed as "validated" unless it passes the following four gates:



1\. \*\*External Ground Truth:\*\* The metric must be tested against an independent, external catalog (e.g., Gaia NSS, DESI Spectroscopy, HGCA). Internal consistency is not sufficient.

2\. \*\*Enrichment Testing:\*\* The metric must demonstrate a monotonic enrichment curve (e.g., higher score = higher probability of ground-truth match).

3\. \*\*Statistical Significance:\*\* Effect sizes (Odds Ratios) and rigorous p-values (Fisher Exact, Permutation Tests) must be reported.

4\. \*\*Independent Predictive Power:\*\* If a metric is a composite of existing variables, it must pass a Logistic Regression test proving it adds explanatory power beyond its raw constituents.



\---



\## 4. Discovery Hierarchy

TRACEBIND strictly adheres to the following nomenclature for anomalies:



\* \*\*Candidate:\*\* An object that scores highly on a TRACEBIND metric but lacks external confirmation. (e.g., "High-Tension Astrometric Anomaly").

\* \*\*Validated:\*\* An object whose TRACEBIND score correlates with an independent catalog flag (e.g., "NSS-Validated Companion Candidate").

\* \*\*Confirmed:\*\* An object with definitive spectroscopic or high-resolution imaging proof of its physical nature (e.g., "DESI-Confirmed Emission-Line Galaxy").



\*TRACEBIND generates Candidates and Validations. Confirmations require external observatories.\*

