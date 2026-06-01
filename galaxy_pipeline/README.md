

\# Galaxy Pipeline



A professional-grade pipeline for identifying uncataloged extragalactic sources (compact blue galaxies, star-forming dwarfs, AGN) using Gaia DR3 astrometry, Pan-STARRS photometry, and Legacy Survey imaging.



\## Methodology



1\. \*\*Gaia query\*\* — low parallax, low proper motion, galaxy-like colors, faint magnitude

2\. \*\*Cross-match\*\* — exclude known objects (SIMBAD, NED, Legacy Survey)

3\. \*\*Extendedness\*\* — PSF vs Kron magnitudes in Pan-STARRS (Δ > 0.5)

4\. \*\*Triangulation\*\* — combine all evidence into confidence score

5\. \*\*Visual inspection\*\* — Legacy Survey cutouts



\## Results



\- \*\*Validated candidate\*\*: Gaia DR3 4575090461821845760

\- \*\*Classification\*\*: Compact Blue Dwarf Galaxy / Star-Forming Compact Galaxy

\- \*\*Properties\*\*: Blue (g-r = -0.17), extended (PSF-Kron ≈ 1.2), no proper motion, no parallax, galaxy probability = 1.0

\- \*\*Status\*\*: Not in SIMBAD, NED, or Legacy Survey catalogs



\## Files



| File | Description |

|------|-------------|

| `batch\_pipeline.py` | Main pipeline script |

| `pipeline\_methodology.md` | Full documentation |

| `final\_candidate\_report.md` | Detailed candidate analysis |

| `batch\_ranked\_candidates.csv` | Prioritized candidate list |

| `candidate\_map.png` | Sky map |

| `legacy\_cutout.png` | Legacy Survey image |



\## Requirements



```bash

pip install -r requirements.txt

```



\## Usage



```bash

python batch\_pipeline.py

```



\## License



CC0 1.0 (Public Domain Dedication)



\---



\*The mirror does not change. You change by seeing yourself in it.\*

```



\---





