
# TRACEBIND: Multi-Survey Reconciliation, Kinematic Mapping & Astrometric Anomaly Ranking

A reproducible survey-reconciliation, candidate-isolation, kinematic-mapping, and anomaly-prioritization framework. This repository contains pipelines for identifying overlooked extragalactic candidates in Gaia DR3, quantifying spatial patterns of directional coherence in the Milky Way, and ranking astrometric model failures to isolate unresolved stellar companions.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Data](https://img.shields.io/badge/Data-Gaia%20DR3%20%7C%20DESI%20%7C%20WISE-orange.svg)

---

## 📊 Current Findings

This project is divided into three primary research pillars:

### Pillar 1: Astrometric Anomaly Ranking (Phase 11)
TRACEBIND's composite astrometric tension metric significantly enriches for Gaia DR3 Non-Single Star (NSS) solutions. Stars in the highest-scoring percentile are approximately six times more likely to belong to Gaia NSS catalogs than baseline stars, and the metric retains independent predictive power beyond RUWE and astrometric excess noise.
* **Validation:** Fisher Exact Test yields an Odds Ratio of 6.12 ($p = 9.44 \times 10^{-6}$) for the top 50 tension targets.
* **Independent Predictive Value:** Logistic regression demonstrates that adding the tension score to a model containing RUWE and Excess Noise nearly doubles the explanatory power (Pseudo-R² increases from 0.1667 to 0.3169).

### Pillar 2: Extragalactic Candidate Isolation (Phases 1-7)
A multi-stage filtering pipeline designed to isolate high-confidence extragalactic candidates overlooked during initial catalog reconciliation.
* **External Validation Case:** The pipeline recovered a DESI-confirmed emission-line galaxy (`z = 0.033`, `ZWARN = 0`; Gaia DR3 `4575090461821845760`), providing an external validation case for the filtering methodology.
* **Statistical Audit Output:** A **12,500-source** unbiased spherical sky baseline that isolated **3** high-priority, mid-infrared excess AGN candidates not identified in the SDSS cross-match used in this study.

### Pillar 3: Galactic Kinematic Coherence Mapping (Phases 9 / D)
An application of directional statistics to quantify localized kinematic coherence in Gaia proper-motion fields.
* **The $C_f$ Metric:** A directional-coherence statistic analytically equivalent to the **Mean Resultant Length ($R$)**.
* **Residual Coherence:** Permutation testing demonstrates that residual directional coherence remains highly significant (**$p < 0.001$**) after subtraction of first-order Galactic rotation (Oort constants) and solar reflex motion, suggesting sensitivity to localized kinematic structure.
* 📄 **[Read the Methodology Paper Prospectus](PAPER_PROSPECTUS.md)**

---

## 🔍 Methodology Overviews

### Pillar 1: Astrometric Tension & NSS Enrichment
Instead of treating Gaia's astrometric noise flags as binary vetoes, TRACEBIND engineers a continuous `tension_score` using logarithmic compression of `RUWE` and `Astrometric Excess Noise`. This composite metric is validated against the Gaia DR3 Non-Single Star (NSS) catalogs to systematically rank stars whose astrometric behavior is inconsistent with a single-star model, prioritizing them for spectroscopic or direct-imaging follow-up.

### Pillar 2: Extragalactic Filtering Funnel
1. **Gaia Query**: Selects sources with low parallax/proper motion significance and high galaxy probability (`> 0.99` via Gaia DR3 DSC CombMod).
2. **Catalog Cross-Match**: Filters out known objects via SIMBAD, NED, and Legacy Survey.
3. **Morphological Scoring**: Calculates extendedness using Pan-STARRS PSF vs. Kron magnitudes (`Δ > 0.5`).
4. **Color Selection**: Identifies star-forming candidates via blue optical colors (`g - r < 0.5`).
5. **High-Energy Validation**: Checks for X-ray/IR counterparts (ROSAT/WISE) to mitigate contamination and identify AGN engines.

### Pillar 3: Kinematic Coherence & Background Subtraction
To test whether coherence remains after subtraction of large-scale Galactic motions, we subtracted the Oort differential rotation and Solar reflex motion (Schönrich et al. 2010). 

| Metric         | Observed | Null Mean | p-value |
| -------------- | -------- | --------- | ------- |
| Mean Coherence | 0.309    | 0.234     | <0.001  |
| Top-5 Mean     | 0.393    | 0.320     | 0.005   |

---

## ⚠️ Limitations & Epistemological Boundary

In accordance with rigorous peer-review standards, this repository explicitly defines the boundaries of its claims:

* **Astrometric Anomalies:** A high tension score is evidence that the catalog description and the observed data deserve closer examination. It is *not* definitive proof of an exoplanet, brown dwarf, or specific companion mass.
* **Kinematic Coherence:** $C_f$ measures directional alignment, not physical association. Significant coherence does not by itself establish membership in stellar streams, nor does it provide evidence for or against Dark Matter, MOND, or Emergent Gravity.
* **Extragalactic Candidates:** Mid-infrared excesses are strongly consistent with AGN activity, but require spectroscopic follow-up for definitive classification.
* **Pending Work:** Cross-matching high-$C_f$ patches against modern 6D phase-space catalogs, and calculating Proper Motion Anomalies (PMa) via the Hipparcos-Gaia Catalog of Accelerations (HGCA) for Phase 11 targets.

---

## 📂 Repository Structure

```text
├── data/                       # Datasets, catalogs, and null distributions
├── figures/                    # Plots, cutouts, enrichment curves, and sky maps
├── reports/                    # Methodology, prospectuses, and candidate logs
├── scripts/
│   ├── phase1_7_agn/           # Extragalactic hunting, PS1, WISE, Crossmatching
│   ├── phase8_9_kinematics/    # Milky Way coherence, Outliers, 3D mapping
│   ├── phaseC_D_statistics/    # Monte Carlo, Permutations, Residuals
│   └── phase11_astrometry/     # Astrometric tension, NSS enrichment, PMa validation
├── PAPER_PROSPECTUS.md         # Prospectus for the directional-statistics methodology paper
├── PHASE_11_PROSPECTUS.md      # Prospectus for the astrometric anomaly ranking framework
├── requirements.txt            # Python dependencies
```

---

## 🚀 Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Astrometric Anomaly Ranking (Phase 11):**
   ```bash
   python scripts/phase11_astrometry/stage_ab_gaia_query.py
   python scripts/phase11_astrometry/phase11a_nss_enrichment_v2.py
   ```

3. **Run the Kinematic Coherence & Permutation Tests:**
   ```bash
   python scripts/phase8_9_kinematics/phase9_allsky_coherence_map.py
   python scripts/phaseC_D_statistics/phase_d_residual_solar_permutation.py
   ```

4. **Run the Extragalactic Discovery Pipeline:**
   ```bash
   python scripts/phase1_7_agn/batch_pipeline_final.py
   ```

---

## 📜 Project Philosophy: Anomaly Prioritization

TRACEBIND does not attempt to replace physical models. It ranks where those models appear strained. 

Modern astronomy generates catalogs of unprecedented scale, but every catalog is built on assumptions: that a source is a single star, that a point of light is a galaxy, that a proper motion vector is linear. When the data violates those assumptions, the catalog description breaks down. A high TRACEBIND score is not evidence of a planet, a binary, a stellar stream, or an AGN. It is evidence that the catalog description and the observed data deserve closer examination.

> *"The universe is not a problem to be solved. It is a transmission to be received."* 
> 📖 **[Read the Full Operator's Manifesto & Project Genesis](reports/MANIFESTO.md)**

---

## 📄 License (CC0 1.0 Universal)

This project is dedicated to the public domain under the **CC0 1.0 Universal** license. 

**No Copyright**
The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law, including all related and neighboring rights, to the extent allowed by law. You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.

**Other Information**
* In no way are the patent or trademark rights of any person affected by CC0, nor are the rights that other persons may have in the work or in how the work is used, such as publicity or privacy rights.
* Unless expressly stated otherwise, the person who associated a work with this deed makes no warranties about the work, and disclaims liability for all uses of the work, to the fullest extent permitted by applicable law.
* When using or citing the work, you should not imply endorsement by the author or the affirmer.
```
