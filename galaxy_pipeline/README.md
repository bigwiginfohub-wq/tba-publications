# Galaxy Pipeline: Extragalactic Candidate Isolation & Survey Reconciliation

A reproducible survey-reconciliation and candidate-isolation framework for identifying extragalactic candidates overlooked during initial catalog reconciliation, using Gaia DR3 astrometry, Pan-STARRS photometry, and Legacy Survey imaging.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)

## 🏆 Results at a Glance

This project produced two distinct scientific outcomes:

### Outcome A: Spectroscopically Validated Object
- **1** DESI-confirmed emission-line galaxy
- **Redshift:** `z = 0.033` (`ZWARN = 0`)
- **Target:** Gaia DR3 `4575090461821845760` (DESI TargetID: `39628450197145219`)

### Outcome B: Statistical Audit Output (TRACEBIND v2.0)
- **12,500-source** unbiased spherical sky baseline
- **12** sources unreconciled across SIMBAD, NED, and SDSS
- **3** high-priority infrared AGN candidates pending spectroscopic follow-up

---

## 🔍 Methodology

The pipeline employs a multi-stage filtering process to isolate high-confidence candidates from raw Gaia data:

1.  **Gaia Query**: Selects sources with low parallax/proper motion significance and high galaxy probability (`> 0.99` via the **Gaia DR3 DSC CombMod classifier**).
2.  **Catalog Cross-Match**: Filters out known objects by cross-referencing SIMBAD, NED, and Legacy Survey catalogs, isolating sources overlooked during initial catalog reconciliation.
3.  **Morphological Scoring**: Calculates extendedness using Pan-STARRS PSF vs. Kron magnitudes (`Δ > 0.5`).
4.  **Color Selection**: Identifies star-forming candidates via blue optical colors (`g - r < 0.5`).
5.  **High-Energy Validation**: Checks for X-ray counterparts (ROSAT/Chandra) to mitigate contamination and identify/rule out active AGN engines.

### 📊 Validation Funnel (Outcome A)

| Pipeline Stage | Objects Remaining | Description |
| :--- | :--- | :--- |
| **Initial Candidate Pool** | ~500 | High-probability Gaia DR3 DSC CombMod galaxy candidates (`classprob_dsc_combmod_galaxy > 0.99`). |
| **Astrometric & Catalog Pre-filtering** | 37 | Filtered for low parallax/PM significance and cross-matched against known catalogs to isolate overlooked sources. |
| **Batch Validation & Scoring** | 37 | Evaluated via Pan-STARRS PSF-Kron extendedness and optical colors; ranked by priority score. |
| **High-Confidence Candidates (Tier 1 & 2)** | 24 | Passed strict morphological (`Δ > 0.5`) and color (`g-r < 0.5`) thresholds (1 T1 Strong, 23 T2 Probable). |
| **Spectroscopically Confirmed** | 1 | Independently validated by DESI DR1 as an emission-line galaxy at `z = 0.033`. |

---

## 🔬 Key Result: Spectroscopic Confirmation

Gaia DR3 source `4575090461821845760` was isolated through astrometric, photometric, and morphological filtering. Subsequent DESI spectroscopy (TargetID `39628450197145219`) classified the object as `GALAXY` at `z = 0.0330` with `ZWARN = 0` (no warning flags on the redshift solution).

- **Pipeline Interpretation**: Compact blue dwarf / star-forming compact galaxy candidate.
- **Initial Catalog Status**: Overlooked during initial reconciliation in SIMBAD, NED, and Legacy Survey DR10.
- **Imaging Morphology**: Extended in Pan-STARRS (`PSF - Kron ≈ 1.18`); classified with a Sérsic profile (`MORPHTYPE = SER`) in deep imaging catalogs.
- **DESI Targeting**: Independently selected by DESI as a Bright Galaxy Survey candidate (`BGS_ANY`).
- **Spectral Features**: DESI spectroscopy revealed prominent nebular emission features, including [O II], Hβ, [O III], Hα, [N II], and [S II], consistent with an emission-line galaxy.

---

## 🛡️ Catalog Auditing & Statistical Baseline (Outcome B)

To ensure the integrity of the candidate list and account for survey selection effects, this pipeline's cross-matching logic is underpinned by the **TRACEBIND v2.0 Identity-Resolution Framework**. TRACEBIND acts as an auditing layer that exposes catalog fragmentation and reconciles disagreements between curated databases (SIMBAD/NED) and automated survey pipelines (SDSS/DESI).

### 🌌 12,500-Source Unbiased Sky Audit
To prove the pipeline's selection criteria were not trivial artifacts, a uniform random-sky baseline of **12,500 Gaia DR3 sources** was generated. This established the "normal" Milky Way stellar background and demonstrated that the target parameter space is rare relative to the sampled Gaia background and enriched in sources that survive successive astrophysical filtering stages.

| Audit Stage | Objects | Scientific Purpose |
| :--- | :--- | :--- |
| **Uniform Sky Baseline** | 12,500 | Unbiased spherical sampling to establish the Milky Way stellar background. |
| **Photometric Selection** | 186 | Applied the pipeline's color/magnitude cuts to the random sky. |
| **Astrometric Purification** | 21 | Filtered for "zero-motion" (Parallax SNR < 2, Total PM < 1 mas/yr). |
| **Catalog Vetting** | 12 | Sources not reconciled within the initial SIMBAD/NED/SDSS matching stage. |
| **Infrared AGN Signature** | **3** | High-priority AGN candidates exhibiting WISE W1−W2 > 1.2 and surviving all reconciliation stages. |

These 3 infrared-bright candidates remain pending spectroscopic follow-up to confirm their extragalactic nature.

Results presented here are consistent with currently available survey evidence and spectroscopic classifications.

---

## 📂 Repository Structure

| Path | Description |
|------|-------------|
| `scripts/` | Pipeline code (`batch_pipeline_v3_1.py`), TRACEBIND audit scripts, validation utilities |
| `data/` | Targeted candidate lists (`batch_ranked_candidates.csv`) & 12,500-source statistical baseline (`gaia_phase1_scaled_10k.csv`) |
| `reports/` | Methodology documentation, candidate reports, and label architecture |
| `figures/` | Visualizations, cutouts, and sky maps |

## 🚀 Usage

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Targeted Discovery Pipeline (Outcome A):**
    ```bash
    python scripts/batch_pipeline_v3_1.py
    ```
    *Check `data/batch_ranked_candidates.csv` for the prioritized list of targets (including the DESI-confirmed galaxy).*

3.  **Run the TRACEBIND v2.0 Statistical Audit (Outcome B):**
    ```bash
    python scripts/gaia_raw_sampler_v4.py
    python scripts/phase4_wise_validation.py
    ```
    *Generates the 12,500-source uniform sky baseline and isolates unreconciled WISE AGN candidates.*

## 📖 Documentation

- **[Pipeline Methodology](reports/pipeline_methodology.md)**: Detailed scoring logic and selection function.
- **[Candidate Report](reports/final_candidate_report.md)**: Deep-dive analysis of the primary validated target.

## 📄 License

This project is dedicated to the public domain under the **CC0 1.0 Universal** license. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.
