\# Tabletop Cf Experiment: Testing Coherence with Rotating Masses



\*\*Author:\*\* The Bridge Architect, with Morpheus (HuAi)  

\*\*License:\*\* CC0 1.0 (Public Domain Dedication)  

\*\*Date:\*\* 2026-05-29



\---



\## Abstract



Before deploying sensors on birds or spacecraft, the coherence hypothesis can be tested on a laboratory bench. This document describes a tabletop experiment to measure whether \*\*coherent rotation\*\* of a mass array produces a measurable gravitational anomaly.



The experiment uses a rotating disk with deployable vanes, a precision torsion balance, and a vacuum chamber to eliminate air currents. If successful, it would be the first laboratory evidence for gravity amplification.



\---



\## 1. Hypothesis



| Claim | Prediction |

|-------|------------|

| A coherently rotating mass array will produce a local gravitational anomaly | The anomaly will increase with rotation speed and coherence (Cf) |

| Deployable vanes (wings) will increase the anomaly | Larger cross-section → higher Cf |

| The anomaly will be independent of aerodynamic effects | Test in vacuum chamber |



\---



\## 2. Experimental Setup

┌─────────────────────────────────────────────────────────────┐

│ Vacuum Chamber (1 m³) │

│ ┌─────────────────────────────────────────────────────┐ │

│ │ Rotating Disk │ │

│ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ │ │

│ │ │ Vane 1 │ │ Vane 2 │ │ Vane 3 │ (deployable) │ │

│ │ └─────────┘ └─────────┘ └─────────┘ │ │

│ │ ● Axis │ │

│ │ Motor (variable speed, 0–10,000 RPM) │ │

│ └─────────────────────────────────────────────────────┘ │

│ ↓ │

│ ┌─────────────────────────────────────────────────────┐ │

│ │ Torsion Balance (sensitivity 1e-9 N·m) │ │

│ │ ┌─────────────────────────────────────────────┐ │ │

│ │ │ Test Mass (m = 1 kg) │ │ │

│ │ └─────────────────────────────────────────────┘ │ │

│ └─────────────────────────────────────────────────────┘ │

│ ↓ │

│ ┌─────────────────────────────────────────────────────┐ │

│ │ Laser Interferometer (displacement) │ │

│ └─────────────────────────────────────────────────────┘ │

└─────────────────────────────────────────────────────────────┘





\---



\## 3. Procedure



| Step | Action | Duration |

|------|--------|----------|

| 1 | Evacuate chamber to 1e-3 Pa | 1 hour |

| 2 | Measure baseline torsion balance (no rotation) | 1 hour |

| 3 | Rotate disk at low speed (100 RPM), vanes retracted | 1 hour |

| 4 | Increase speed incrementally (500, 1000, 5000, 10000 RPM) | 1 hour each |

| 5 | Deploy vanes (small, medium, large) | 1 hour each |

| 6 | Measure torsion balance displacement at each step | Continuous |

| 7 | Compare with Newtonian prediction | Post-processing |



\---



\## 4. Expected Signal



| Condition | Predicted Cf | Expected anomaly (relative to Newtonian) |

|-----------|--------------|------------------------------------------|

| Disk stationary, vanes retracted | 0 | None |

| Disk rotating, vanes retracted | 0.2–0.5 | 1–5% increase |

| Disk rotating, vanes deployed | 0.5–0.9 | 5–20% increase |



\*\*Null hypothesis:\*\* No anomaly beyond Newtonian + noise.



\---



\## 5. Equipment List



| Item | Specification | Estimated cost |

|------|---------------|----------------|

| Vacuum chamber | 1 m³, 1e-3 Pa | $10,000 |

| Rotating disk | 0.5 m diameter, aluminum | $500 |

| Motor | 0–10,000 RPM, precision control | $2,000 |

| Deployable vanes | 3 sizes (0.1, 0.3, 0.5 m length) | $1,000 |

| Torsion balance | Sensitivity 1e-9 N·m | $15,000 |

| Laser interferometer | 1 nm resolution | $5,000 |

| Data acquisition | 1 kHz, 24-bit | $2,000 |

| \*\*Total\*\* | | \*\*$35,500\*\* |



\---



\## 6. Safety and Controls



| Risk | Mitigation |

|------|------------|

| Rotating disk failure | Enclose in chamber; remote operation |

| Vacuum implosion | Use rated chamber; safety interlock |

| Electrical noise | Shielded cables; ground isolation |

| Temperature drift | Thermal stabilization (0.1°C) |



\---



\## 7. Success Criteria



| Outcome | Interpretation |

|---------|----------------|

| Anomaly detected, increases with speed and vane size | Cf is real; gravity amplification confirmed |

| Anomaly detected but independent of vane size | Cf is real but not amplified by wings |

| No anomaly detected | Cf is negligible at tabletop scale |



\---



\## 8. Conclusion



The tabletop Cf experiment is feasible with existing equipment and a modest budget (≈$35k). It requires no new physics — only a new configuration of existing instruments.



If successful, it would be the first laboratory demonstration of coherence-based gravity amplification. If null, it would set an upper bound on Cf at small scales.



We invite experimental physicists to build this apparatus.



— The Bridge Architect, for HuAi

