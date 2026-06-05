
# TRACEBIND: Multi-Survey Reconciliation & Galactic Kinematic Framework

A reproducible survey-reconciliation, candidate-isolation, and kinematic-mapping framework. This repository contains the complete pipeline for identifying overlooked extragalactic candidates in Gaia DR3, as well as the TRACEBIND methodology for quantifying spatial patterns of directional coherence in Gaia proper-motion fields.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Data](https://img.shields.io/badge/Data-Gaia%20DR3%20%7C%20DESI%20%7C%20WISE-orange.svg)

---

## 📊 Current Findings

This project is divided into two primary research pillars:

### Pillar 1: Extragalactic Candidate Isolation
A multi-stage filtering pipeline designed to isolate high-confidence extragalactic candidates overlooked during initial catalog reconciliation.
* **External Validation Case:** The pipeline recovered a DESI-confirmed emission-line galaxy (`z = 0.033`, `ZWARN = 0`; Gaia DR3 `4575090461821845760`), providing an external validation case for the filtering methodology.
* **Statistical Audit Output:** A **12,500-source** unbiased spherical sky baseline that isolated **3** high-priority infrared AGN candidates pending spectroscopic follow-up.

### Pillar 2: Galactic Kinematic Coherence Mapping (Phase 9 / Phase D)
An application of directional statistics to quantify localized kinematic coherence in Gaia proper-motion fields.
* **The $C_f$ Metric:** A directional-coherence statistic analytically equivalent to the **Mean Resultant Length ($R$)**.
* **Residual Coherence:** Permutation testing demonstrates that residual directional coherence remains highly significant (**$p < 0.001$**) after subtraction of first-order Galactic rotation (Oort constants) and solar reflex motion, suggesting sensitivity to localized kinematic structure.
* 📄 **[Read the Methodology Paper Prospectus](PAPER_PROSPECTUS.md)**

---

## 🔍 Pillar 1: Extragalactic Methodology

The pipeline employs a multi-stage filtering process to isolate high-confidence candidates from raw Gaia data:

1. **Gaia Query**: Selects sources with low parallax/proper motion significance and high galaxy probability (`> 0.99` via Gaia DR3 DSC CombMod).
2. **Catalog Cross-Match**: Filters out known objects via SIMBAD, NED, and Legacy Survey.
3. **Morphological Scoring**: Calculates extendedness using Pan-STARRS PSF vs. Kron magnitudes (`Δ > 0.5`).
4. **Color Selection**: Identifies star-forming candidates via blue optical colors (`g - r < 0.5`).
5. **High-Energy Validation**: Checks for X-ray/IR counterparts (ROSAT/WISE) to mitigate contamination and identify AGN engines.

### Validation Funnel

| Pipeline Stage | Objects Remaining | Description |
| :--- | :--- | :--- |
| **Initial Candidate Pool** | ~500 | High-probability Gaia DR3 DSC CombMod galaxy candidates. |
| **Astrometric Pre-filtering** | 37 | Filtered for low parallax/PM significance. |
| **Batch Validation & Scoring** | 37 | Evaluated via Pan-STARRS PSF-Kron extendedness and optical colors. |
| **High-Confidence Candidates** | 24 | Passed strict morphological and color thresholds. |
| **Spectroscopically Confirmed** | **1** | Independently validated by DESI DR1 (`z = 0.033`). |

---

## 🌌 Pillar 2: Kinematic Coherence & TRACEBIND Auditing

To ensure the integrity of candidate lists and map local Galactic structure, the pipeline generates an unbiased **12,500-source spherical sky baseline**. This baseline is used both to audit catalog fragmentation and to compute the all-sky Kinematic Coherence Map ($C_f$).

### The Phase D Residual Permutation Test
To test whether coherence remains after subtraction of large-scale Galactic motions, we subtracted the Oort differential rotation and Solar reflex motion (Schönrich et al. 2010). 

| Metric         | Observed | Null Mean | p-value |
| -------------- | -------- | --------- | ------- |
| Mean Coherence | 0.309    | 0.234     | <0.001  |
| Top-5 Mean     | 0.393    | 0.320     | 0.005   |

*Conclusion: Residual directional coherence remains significantly above randomized expectations after subtraction of first-order Galactic background motions.*

---

## ⚠️ Limitations

* $C_f$ is equivalent to the Mean Resultant Length and therefore measures directional alignment, not physical association.
* Significant coherence does not by itself establish membership in stellar streams or moving groups.
* Current background subtraction uses a first-order Galactic model.
* Current analysis uses proper motions and parallax only; radial velocities are available for only a subset of Gaia DR3 sources.
* High-coherence regions have not yet been systematically cross-matched against modern 6D phase-space catalogs.
* Significant residual coherence does not by itself imply the discovery of new stellar structures.

---

## 🛡️ Epistemological Boundary

In accordance with rigorous peer-review standards, this repository explicitly defines the boundaries of its claims:
* **Established:** $C_f$ is analytically equivalent to the Mean Resultant Length ($R$). Gaia proper-motion fields exhibit statistically significant residual directional coherence.
* **Not Established:** The pipeline does *not* claim to have discovered new stellar streams, nor does it provide evidence for or against Dark Matter, MOND, or Emergent Gravity. 
* **Pending:** Cross-matching high-$C_f$ patches against modern 6D phase-space substructure catalogs.

---

## 📂 Repository Structure

```text
├── data/                       # Datasets, catalogs, and null distributions
├── figures/                    # Plots, cutouts, and sky maps
├── reports/                    # Methodology, prospectuses, and candidate logs
├── scripts/
│   ├── phase1_7_agn/           # Extragalactic hunting, PS1, WISE, Crossmatching
│   ├── phase8_9_kinematics/    # Milky Way coherence, Outliers, 3D mapping
│   └── phaseC_D_statistics/    # Monte Carlo, Permutations, Residuals
├── PAPER_PROSPECTUS.md         # Prospectus for the directional-statistics methodology paper
├── requirements.txt            # Python dependencies
```

---

## 🚀 Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Extragalactic Discovery Pipeline:**
   ```bash
   python scripts/phase1_7_agn/batch_pipeline_final.py
   ```

3. **Run the Kinematic Coherence & Permutation Tests:**
   ```bash
   python scripts/phase8_9_kinematics/phase9_allsky_coherence_map.py
   python scripts/phaseC_D_statistics/phase_d_residual_solar_permutation.py
   ```

## 📖 Documentation

- **[Pipeline Methodology](reports/pipeline_methodology.md)**: Detailed scoring logic and selection function.
- **[Candidate Report](reports/final_candidate_report.md)**: Deep-dive analysis of the primary validated target.

---

## 📜 Project Philosophy

> *"The universe is not a problem to be solved. It is a transmission to be received."* 
> 📖 **[Read the Operator's Manifesto & Project Genesis](reports/MANIFESTO.md)**

---

## 📄 License

This project is dedicated to the public domain under the **CC0 1.0 Universal** license. 

The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law, including all related and neighboring rights, to the extent allowed by law. You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.
```

