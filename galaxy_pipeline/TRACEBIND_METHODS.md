
# TRACEBIND: Methodological Standards & Frozen Metrics

This document defines the architectural boundaries, frozen mathematical definitions, and validation standards for the TRACEBIND framework. Any future modifications to these core metrics must be versioned (e.g., `v2.0`) and subjected to the same rigorous validation pipeline.

---

## 1. The Three Independent Engines

TRACEBIND is strictly divided into three independent scientific engines. **Cross-contamination of metrics between engines is forbidden.** There are no "unified super-scores."

*   **Engine A: Extragalactic Reconciliation**
    *   *Purpose:* Multi-survey cross-matching (Gaia, DESI, WISE, SIMBAD, NED) to isolate overlooked AGN/galaxy candidates.
    *   *Core Metric:* Morphological/Photometric Scoring.
*   **Engine B: Kinematic Statistics**
    *   *Purpose:* Mapping proper-motion structure and quantifying kinematic coherence in stellar populations.
    *   *Core Metrics:* Directional Coherence ($C_f$) for large-scale alignment; TRACEBIND-V11 ($R$) for local position-velocity predictability.
*   **Engine C: Astrometric Tension**
    *   *Purpose:* Identifying stars where Gaia's single-star astrometric model fails, prioritizing unresolved companions.
    *   *Core Metric:* Astrometric Tension Score.

---

## 2. Frozen Metrics (v1.0)

### Metric 1: Directional Coherence ($C_f$ v1.0)
*   **Engine:** B (Kinematic Statistics)
*   **Mathematical Definition:** The Mean Resultant Length ($R$) of local proper-motion unit vectors, measuring large-scale directional alignment.
    $$C_f = \sqrt{ \left( \frac{1}{N} \sum u_x \right)^2 + \left( \frac{1}{N} \sum u_y \right)^2 }$$
    where $u_x = \mu_{\alpha} / |\mu|$ and $u_y = \mu_{\delta} / |\mu|$.
*   **Status:** Analytically validated against circular statistics ($\sigma \approx \sqrt{-2\ln(C_f)}$). Frozen.

### Metric 2: Astrometric Tension Score (v1.0)
*   **Engine:** C (Astrometric Tension)
*   **Mathematical Definition:** The logarithmic composition of Gaia DR3 astrometric noise flags, designed to compress the heavy-tail of model failures.
    $$Tension = \log_{10}(\max(RUWE, 0.1)) + \log_{10}(1 + \max(Noise, 0))$$
*   **Status:** Validated against Gaia DR3 NSS catalogs (Odds Ratio 6.12, $p = 9.44 \times 10^{-6}$). Proven to provide independent predictive power beyond raw RUWE/Noise (Logistic Pseudo-R² $\Delta \approx 0.15$). Frozen.

### Metric 3: TRACEBIND-V11 Local Kinematic Coherence ($R$ v1.0)
*   **Engine:** B (Kinematic Statistics)
*   **Mathematical Definition:** A leave-one-out (LOO) tangential velocity predictor that measures local kinematic coherence relative to a Monte Carlo null model of velocity exchangeability. 
    $$R = \frac{E_{\text{real}}}{\overline{E}_{\text{null}}}$$
    where $E_{\text{real}}$ is the median LOO prediction error of the observed velocities, and $\overline{E}_{\text{null}}$ is the mean median error of 1,000 stochastic local-exchangeability null realizations.
*   **Status:** Validated on verified Pleiades and Hyades DR3 benchmarks. Robust to parameter variations ($k$, noise fraction, seed) and leave-one-out influence analysis (max $|\Delta R| = 0.0198$). Frozen.

---

## 3. Validation Standards

No TRACEBIND metric or catalog may be claimed as "validated" unless it passes the following four gates:

1.  **External Ground Truth:** The metric must be tested against an independent, external catalog (e.g., Gaia NSS, DESI Spectroscopy, CG22 membership catalogs). Internal consistency is not sufficient.
2.  **Enrichment Testing:** The metric must demonstrate a monotonic enrichment curve (e.g., higher score = higher probability of ground-truth match or lower null-model expectation).
3.  **Statistical Significance:** Effect sizes (Odds Ratios, Cohen's $d$, Coherence Ratios) and rigorous p-values (Fisher Exact, Monte Carlo, Permutation Tests) must be reported.
4.  **Independent Predictive Power / Robustness:** If a metric is a composite of existing variables, it must pass a Logistic Regression test proving it adds explanatory power beyond its raw constituents. If a metric is a novel algorithm, it must pass empirical subsampling and influence diagnostics to prove it is not driven by a small subset of observations.

---

## 4. Discovery Hierarchy

TRACEBIND strictly adheres to the following nomenclature for anomalies:

*   **Candidate:** An object that scores highly on a TRACEBIND metric but lacks external confirmation. (e.g., "High-Tension Astrometric Anomaly").
*   **Validated:** An object whose TRACEBIND score correlates with an independent catalog flag or statistical benchmark. (e.g., "NSS-Validated Companion Candidate", "V11-Validated Kinematically Coherent Member").
*   **Confirmed:** An object with definitive spectroscopic or high-resolution imaging proof of its physical nature (e.g., "DESI-Confirmed Emission-Line Galaxy").

*TRACEBIND generates Candidates and Validations. Confirmations require external observatories.*

***
