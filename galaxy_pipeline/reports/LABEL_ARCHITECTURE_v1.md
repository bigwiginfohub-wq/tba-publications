\# LABEL\_ARCHITECTURE\_v1.md

\*\*Project:\*\* TRACEBIND\_v2.0 Coherence Pipeline

\*\*Date:\*\* 2026-06-03

\*\*Status:\*\* FROZEN for Phase 1C Data Collection



\## 1. Label Confidence Tiers

Labels are derived exclusively from external, independent catalogs (currently SIMBAD) to prevent Gaia-internal circular learning.



| Tier | Classification | SIMBAD OTYPE Triggers (Case-Insensitive) | Scientific Meaning |

|------|----------------|------------------------------------------|--------------------|

| \*\*Tier 1\*\* | Extragalactic\_High | `AGN`, `QSO`, `EMG`, `GRG`, `LSB`, `BCG`, `GXY`, `G`, `SY1`, `SY2` | Trusted positive. High-confidence galaxy/AGN. |

| \*\*Tier 2\*\* | Extragalactic\_Candidate | `AG?`, `G?`, `CANDIDATE` | Weaker positive. Plausible extragalactic object. |

| \*\*Tier 1\*\* | Stellar\_High | `STAR`, `PM\*`, `WD\*`, `Y\*O`, `IR\*`, `WR\*`, `\*` | Trusted negative. Confirmed star/contaminant. |

| \*\*Tier 3\*\* | Ambiguous | Any other valid SIMBAD OTYPE | Excluded from supervised training. Requires manual review. |

| \*\*Tier 0\*\* | Unknown | No SIMBAD match within query radius | Unlabeled. Cannot be used as ground truth. |



\## 2. Crossmatch Quality Flags

Based on angular separation between Gaia candidate and SIMBAD match:

\- \*\*Excellent\*\*: $\\le 0.2$ arcsec

\- \*\*Good\*\*: $> 0.2$ and $\\le 0.5$ arcsec

\- \*\*Review\*\*: $> 0.5$ arcsec (Flagged for potential chance association)



\## 3. Anti-Leakage Boundary Statement

Under no circumstances will Gaia-derived internal ML probabilities (e.g., `classprob\_dsc\_combmod\_galaxy`) or astrometric heuristic scores (e.g., `ruwe`, `astrometric\_excess\_noise`) be used to generate ground truth labels. They may only be used as input features for the model.

