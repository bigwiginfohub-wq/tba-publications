# Galaxy Pipeline: Extragalactic Candidate Isolation & Survey Reconciliation

A reproducible survey-reconciliation and candidate-isolation framework for identifying extragalactic candidates overlooked during initial catalog reconciliation, using Gaia DR3 astrometry, Pan-STARRS photometry, and Legacy Survey imaging.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)

## 🔍 Methodology

The pipeline employs a multi-stage filtering process to isolate high-confidence candidates from raw Gaia data:

1.  **Gaia Query**: Selects sources with low parallax/proper motion significance and high galaxy probability (`> 0.99` via the **Gaia DR3 DSC CombMod classifier**).
2.  **Catalog Cross-Match**: Filters out known objects by cross-referencing SIMBAD, NED, and Legacy Survey catalogs, isolating sources overlooked during initial catalog reconciliation.
3.  **Morphological Scoring**: Calculates extendedness using Pan-STARRS PSF vs. Kron magnitudes (`Δ > 0.5`).
4.  **Color Selection**: Identifies star-forming candidates via blue optical colors (`g - r < 0.5`).
5.  **High-Energy Validation**: Checks for X-ray counterparts (ROSAT/Chandra) to mitigate contamination and identify/rule out active AGN engines.

## 📊 Validation Summary

| Pipeline Stage | Objects Remaining |
| :--- | :--- |
| Initial Gaia Selection | `[Insert Number]` |
| Morphological Filter (PS1) | `[Insert Number]` |
| Cross-Match Reconciliation | `[Insert Number]` |
| Final Candidate Set | 37 |
| Spectroscopically Confirmed | 1 |

## 🏆 Key Results: Spectroscopic Confirmation

Gaia DR3 source `4575090461821845760` was isolated through astrometric, photometric, and morphological filtering. Subsequent DESI spectroscopy (TargetID `39628450197145219`) classified the object as `GALAXY` at `z = 0.0330` with `ZWARN = 0` (no warning flags on the redshift solution).

- **Pipeline Interpretation**: Compact blue dwarf / star-forming compact galaxy candidate.
- **Initial Catalog Status**: Overlooked during initial reconciliation in SIMBAD, NED, and Legacy Survey DR10.
- **Imaging Morphology**: Extended in Pan-STARRS (`PSF - Kron ≈ 1.18`); classified with a Sérsic profile (`MORPHTYPE = SER`) in deep imaging catalogs.
- **DESI Targeting**: Independently selected by DESI as a Bright Galaxy Survey candidate (`BGS_ANY`).
- **Spectral Features**: DESI spectroscopy revealed prominent nebular emission features, including [O II], Hβ, [O III], Hα, [N II], and [S II], consistent with an emission-line galaxy.

## 🛡️ Catalog Auditing & Reconciliation (TRACEBIND v2.0)

To ensure the integrity of the candidate list and account for survey selection effects, this pipeline's cross-matching logic is underpinned by the **TRACEBIND v2.0 Identity-Resolution Framework**. TRACEBIND acts as an auditing layer that:
- Exposes catalog fragmentation across SIMBAD, NED, and deep imaging surveys.
- Enforces strict geometric and multi-wavelength cross-matching to mitigate contamination from high-proper-motion stellar interlopers.
- Reconciles disagreements between curated databases and automated survey pipelines (e.g., SDSS/DESI), ensuring that the absence of an object in a specific catalog is rigorously vetted before proceeding to morphological scoring.

Results presented here are consistent with currently available survey evidence and spectroscopic classifications.

## 📂 Repository Structure

| Path | Description |
|------|-------------|
| `scripts/` | Pipeline code (`batch_pipeline_v3_1.py`), validation utilities |
| `data/` | Input candidate lists & ranked output CSVs |
| `reports/` | Methodology documentation & candidate reports |
| `figures/` | Visualizations, cutouts, and sky maps |

## 🚀 Usage

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the pipeline:**
    ```bash
    python scripts/batch_pipeline_v3_1.py
    ```

3.  **Review results:**
    Check `data/batch_ranked_candidates.csv` for the prioritized list of targets.

## 📖 Documentation

- **[Pipeline Methodology](reports/pipeline_methodology.md)**: Detailed scoring logic and selection function.
- **[Candidate Report](reports/final_candidate_report.md)**: Deep-dive analysis of the primary validated target.

## 📄 License

This project is dedicated to the public domain under the **CC0 1.0 Universal** license. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.
