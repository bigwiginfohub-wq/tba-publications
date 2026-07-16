
# TRACEBIND: A Modular Framework for Survey Reconciliation and Kinematic Coherence

A reproducible survey-reconciliation, candidate-isolation, kinematic-mapping, and anomaly-prioritization framework. This repository contains pipelines for identifying overlooked extragalactic candidates in Gaia DR3, quantifying spatial patterns of directional coherence in the Milky Way, and ranking astrometric model failures to isolate unresolved stellar companions.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Data](https://img.shields.io/badge/Data-Gaia%20DR3%20%7C%20DESI%20%7C%20WISE-orange.svg)

---

## 📊 Current Findings

TRACEBIND is a modular research framework consisting of independent but related analysis pipelines sharing common principles of validation, reproducibility, and cross-survey reconciliation.

### Pillar 1: Astrometric Anomaly Ranking & Companion Discovery (Phase 11–12)
TRACEBIND combines astrometric and astrophysical features to identify stars whose observed behavior is inconsistent with a single-star model.

* **NSS Enrichment:** High-tension stars are significantly enriched in Gaia DR3 Non-Single Star (NSS) solutions relative to baseline populations.
* **Machine Learning Validation:** A combined astrometric + astrophysical model achieves **ROC-AUC = 0.9522 ± 0.0026**, demonstrating near-perfect discrimination between NSS and non-NSS systems.
* **Physical-Origin Investigation:** Follow-up crossmatches indicate that elevated tension is not primarily explained by ultraviolet activity or cataloged optical variability.
* **Multiplicity Enrichment:** TRACEBIND candidates show significant enrichment in known visual and spectroscopic binaries (WDS/SB9), supporting unresolved multiplicity as a major physical origin of astrometric tension.

### Pillar 2: Extragalactic Candidate Isolation (Phases 1-7)
A multi-stage filtering pipeline designed to isolate high-confidence extragalactic candidates overlooked during initial catalog reconciliation.
* **External Validation Case:** The pipeline recovered a DESI-confirmed emission-line galaxy (`z = 0.033`, `ZWARN = 0`; Gaia DR3 `4575090461821845760`), providing an external validation case for the filtering methodology.
* **Statistical Audit Output:** A **12,500-source** unbiased spherical sky baseline that isolated **3** high-priority, mid-infrared excess AGN candidates not identified in the SDSS cross-match used in this study.

### Pillar 3: Kinematic Coherence Mapping (TRACEBIND-V11)
A quantitative observable for local position–velocity coherence, measuring the degree to which spatial proximity predicts velocity similarity beyond local density and dispersion alone. Distinct from gravitational binding; coherent populations (e.g., tidal streams) are not necessarily bound.

-   **Verified Benchmarks:** Fully audited DR3 samples for Pleiades (N=749) and Hyades (N=820) constructed via official `gaiaedr3.dr2_neighbourhood` cross-match. All intermediate artifacts preserved for auditability.
-   **Parameter Robustness:** Comparative ordering (Hyades R < Pleiades R) preserved across all 36 tested parameter combinations (k ∈ {20,30,40,50}, noise ∈ {0.05,0.10,0.20}, seeds {42,100,2024}). Mean ΔR = 0.069 ± 0.011.
-   **Empirical Subsampling Stability:** 500 replicates × 80% fraction without replacement. Pleiades CV = 0.014, Hyades CV = 0.037 (~2.7× greater variability). Differential variability reproducible across random seeds (cross-seed range < 0.003). Physical interpretations remain hypotheses requiring further investigation.
-   **Statistical Significance:** Both clusters show prediction errors significantly smaller than Monte Carlo null expectations (Pleiades p=0.003, Hyades p=0.002).
-   **Influence Robustness:** Leave-one-out analysis confirms no single star dominates the Hyades coherence ratio (max |ΔR| = 0.0198).
-   **Orthogonal Diagnostics:** Projected outflow analysis confirms V11 captures local predictability independent of bulk expansion dynamics.
-   **Frozen Configuration:** k=30, N_permutations=1000, noise_fraction=0.10, seed=42. See `/scripts/gaia_cf/` for full implementation.

---

## 🔬 Phase 12: Physical-Origin Investigation

TRACEBIND was designed to identify catalog-model tension, not to assume a physical explanation. Phase 12 therefore tests competing hypotheses for the origin of high-tension systems.

### Activity Hypothesis
Pilot crossmatches against ultraviolet and optical-variability catalogs were performed using matched-control samples.
**Results:** No significant enrichment in GALEX NUV detection or TIC cataloged variables relative to controls.

### Multiplicity Hypothesis
Crossmatches against the Washington Double Star (WDS) catalog and the Ninth Catalogue of Spectroscopic Binary Orbits (SB9) reveal:
* **TRACEBIND Targets:** 70.0% present in WDS/SB9
* **Matched Controls:** 36.7% present in WDS/SB9
* **Fisher Exact Test:** p = 9.55 × 10⁻³ (Odds Ratio ≈ 4.03)

This provides direct evidence that astrometric tension is strongly associated with unresolved multiplicity.

---
---

## ⚠️ Limitations & Epistemological Boundary

In accordance with rigorous peer-review standards, this repository explicitly defines the boundaries of its claims:

* **Astrometric Anomalies:** A high tension score is evidence that the catalog description and the observed data deserve closer examination. It is *not* definitive proof of an exoplanet, brown dwarf, or specific companion mass.
* **Kinematic Coherence ($C_f$):** Measures directional alignment, not physical association. Significant coherence does not by itself establish membership in stellar streams, nor does it provide evidence for or against Dark Matter, MOND, or Emergent Gravity.
* **Extragalactic Candidates:** Mid-infrared excesses are strongly consistent with AGN activity, but require spectroscopic follow-up for definitive classification.
* **Local Coherence (V11):** Detects statistically significant position–velocity structure but does not yet propagate measurement uncertainties through the predictor. Hyades-specific subsampling sensitivity has been tested on one cluster only; generalization to older/diffuse clusters remains unproven. Evaluation on additional independently vetted open clusters spanning ages and dynamical states is required.
---

## 📂 Repository Structure

```text
├── data/                       # Datasets, Master Catalog, and DR4 Time Capsule
├── figures/                    # Plots, enrichment curves, HR diagrams, and sky maps
├── reports/                    # Methodology, prospectuses, and candidate logs
├── scripts/
│   ├── phase1_7_agn/           # Extragalactic hunting, PS1, WISE, Crossmatching
│   ├── phase8_9_kinematics/    # Milky Way coherence, Outliers, 3D mapping
│   ├── phaseC_D_statistics/    # Monte Carlo, Permutations, Residuals
│   ├── phase11_astrometry/     # Astrometric tension, NSS enrichment, ML validation
│   ├── phase12_physical_origin/# GALEX, TIC, WDS/SB9 multiplicity crossmatches
│   └── gaia_cf/                # TRACEBIND-V11 Metric & Benchmarks
│           ├── tracebind_v11_core.py
│           ├── compute_subsample_stability.py
│           ├── plot_subsample_distributions.py
│           ├── verify_subsample_stability.py
│           ├── analyze_v11_influence.py       # Leave-one-out influence analysis
│           ├── diagnose_hyades_influence.py   # Spatial & property diagnostics
│           ├── verify_graph_diagnostics.py    # Graph structure verification
│           └── analyze_tangential_outflow.py  # Projected outflow analysis
├── PAPER_PROSPECTUS.md         # Prospectus for the directional-statistics methodology paper
├── PHASE_11_PROSPECTUS.md      # Prospectus for the astrometric anomaly ranking framework
├── TRACEBIND_METHODS.md        # Frozen metrics (v1.0) and validation standards
├── requirements.txt            # Python dependencies
```

---

## 🚀 Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Master Pipeline (Astrometric Anomaly Ranking):**
   ```bash
   python tracebind_pipeline.py
   ```

3. **Run the Kinematic Coherence & Permutation Tests:**
   ```bash
   python scripts/phase8_9_kinematics/phase9_allsky_coherence_map.py
   python scripts/phaseC_D_statistics/phase_d_residual_solar_permutation.py
   ```

4.  **Run TRACEBIND-V11 Benchmark Construction & Analysis:**
    ```bash
    python scripts/gaia_cf/compute_subsample_stability.py
    python scripts/gaia_cf/plot_subsample_distributions.py
    ```
    **Run Advanced Diagnostics (Influence & Outflow):**
    ```bash
    python scripts/gaia_cf/analyze_v11_influence.py
    python scripts/gaia_cf/analyze_tangential_outflow.py
    ```
    See `/scripts/gaia_cf/` for full pipeline including benchmark construction, robustness audits, and visualization.
   ```

5. **Run the Extragalactic Discovery Pipeline:**
   ```bash
   python scripts/phase1_7_agn/batch_pipeline_final.py
   ```
---

## 📜 Project Philosophy: Discovery Through Model Failure

TRACEBIND is built on a simple principle:

> Scientific discovery often begins where a successful model starts to fail.

Astronomical catalogs are built from assumptions: that a source is a single star, that a proper motion is linear, that a point source is adequately described by a particular model. Most of the time these assumptions work remarkably well.

Sometimes they do not.

TRACEBIND does not attempt to replace those models. Instead, it systematically measures where observed data and catalog descriptions diverge. Those divergences are ranked, validated, and stress-tested against independent datasets.

The goal is not anomaly detection for its own sake. The goal is to identify astrophysical populations that existing catalog frameworks only partially describe.

In this sense, TRACEBIND functions as a discovery engine for catalog-model tension: a reproducible framework for turning model failures into scientifically testable hypotheses.

> *"The universe is not a problem to be solved. It is a transmission to be received."* 
> 📖 **[Read the Full Operator's Manifesto & Project Genesis](reports/MANIFESTO.md)**

---

## 📄 License (CC0 1.0 Universal)

This project is dedicated to the public domain under the **CC0 1.0 Universal** license. 

**No Copyright**
The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law, including all related and neighboring rights, to the extent allowed by law. You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.
```
