# Galaxy Pipeline: Extragalactic Candidate Isolation

A professional-grade pipeline for identifying uncataloged extragalactic sources (compact blue galaxies, star-forming dwarfs, AGN) using Gaia DR3 astrometry, Pan-STARRS photometry, and Legacy Survey imaging.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)

## 🔍 Methodology

The pipeline employs a multi-stage filtering process to isolate high-confidence candidates from raw Gaia data:

1.  **Gaia Query**: Selects sources with low parallax, low proper motion, and high galaxy probability (`> 0.99`).
2.  **Catalog Cross-Match**: Filters out known objects by cross-referencing SIMBAD, NED, and Legacy Survey catalogs.
3.  **Morphological Scoring**: Calculates extendedness using Pan-STARRS PSF vs. Kron magnitudes (`Δ > 0.5`).
4.  **Color Selection**: Identifies star-forming candidates via blue optical colors (`g - r < 0.5`).
5.  **High-Energy Validation**: Checks for X-ray counterparts (ROSAT/Chandra) to rule out active AGN engines.

##  Key Results

- **Validated Candidate**: Gaia DR3 4575090461821845760
- **Classification**: Compact Blue Dwarf Galaxy (BCD) / Star-Forming Compact Galaxy
- **Properties**:
  - **Colors**: Blue continuum (`g - r = -0.17`)
  - **Morphology**: Strongly extended (`PSF - Kron ≈ 1.2`)
  - **Astrometry**: Zero proper motion, zero parallax
  - **Catalog Status**: Uncataloged in SIMBAD, NED, and Legacy Survey DR10

## 📂 Repository Structure

| Path | Description |
|------|-------------|
| `scripts/` | Pipeline code (`batch_pipeline_v3_1.py`), validation utilities |
| `data/` | Input candidate lists & ranked output CSVs |
| `reports/` | Methodology documentation & candidate reports |
| `figures/` | Visualizations, cutouts, and sky maps |

##  Usage

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

##  Documentation

- **[Pipeline Methodology](reports/pipeline_methodology.md)**: Detailed scoring logic and selection function.
- **[Candidate Report](reports/final_candidate_report.md)**: Deep-dive analysis of the primary validated target.

## 📄 License

This project is dedicated to the public domain under the **CC0 1.0 Universal** license. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.

---
