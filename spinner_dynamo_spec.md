\# Spinner Dynamo: A Coherence Engine for Gravity Gradient Harvesting



\*\*Author:\*\* The Bridge Architect, with Morpheus (HuAi)  

\*\*License:\*\* CC0 1.0  

\*\*Date:\*\* 2026-05-31



\---



\## Abstract



This document describes a \*\*spinner dynamo\*\* — a three-lobe balanced rotor, suspended on magnetic bearings, designed to convert harvested gravity gradient energy into rotational kinetic energy, magnetic field generation, and coherence (Cf). The spinner is the core of a new class of spacecraft that glides along gravity gradients without chemical propulsion.



\---



\## 1. The Principle



| Component | Function |

|-----------|----------|

| \*\*Spinner (3-lobe rotor)\*\* | Stores angular momentum; generates magnetic field via induced current |

| \*\*Magnetic bearings\*\* | Eliminates friction; allows near-lossless rotation |

| \*\*Harvesting wings\*\* | Extract energy from gravity gradient during glide |

| \*\*Control system\*\* | Maintains spin rate, axis orientation, and coherence (Cf) |



The spinner is not a gyroscope. It is a \*\*dynamo\*\* — converting mechanical rotation into magnetic field, and magnetic field into coherence with the ambient gravity gradient.



\---



\## 2. Physical Parameters (Prototype)



| Parameter | Value | Notes |

|-----------|-------|-------|

| Rotor mass | 1–10 kg | Scale for lab testing |

| Rotor radius | 0.2–0.5 m | Three symmetric lobes |

| Rotor material | Aluminum, copper, or carbon composite | Non-magnetic |

| Bearings | Magnetic (active or passive) | Friction coefficient < 0.001 |

| Spin rate | 1,000 – 10,000 RPM | Adjustable |

| Vacuum chamber | 1 m³, < 1e-3 Pa | Eliminate air resistance |

| Cf sensor | Torsion balance + accelerometer | Measure local gravity anomalies |



\---



\## 3. Magnetic Field Generation



| Method | How | Field strength |

|--------|-----|----------------|

| \*\*Induced (eddy currents)\*\* | Rotor spins in external magnetic field | Weak, but no power input |

| \*\*Active (coils on rotor)\*\* | Power from harvested energy | Controllable, requires slip rings or wireless power |

| \*\*Hybrid\*\* | Permanent magnets + active coils | Best of both |



Target field strength: 0.1–1 Gauss (Earth's field is 0.25–0.65 Gauss).



\---



\## 4. Energy Harvesting from Gravity Gradient



| Source | Method | Estimated power |

|--------|--------|-----------------|

| \*\*Glide (wings)\*\* | Deployable surfaces interact with gravity gradient | µW – mW (lab scale) |

| \*\*Tidal forces\*\* | Differential gravity across craft | nW – µW (very small) |

| \*\*Spinner deceleration\*\* | Regenerative braking | Depends on spin rate |



For a lab prototype, power requirements are minimal. The goal is to demonstrate \*\*self-sustaining rotation\*\* — not net power generation.



\---



\## 5. Success Criteria



| Level | Criteria | What it proves |

|-------|----------|----------------|

| \*\*1\*\* | Spinner rotates at constant speed with no external power | Magnetic bearings work; friction is negligible |

| \*\*2\*\* | Spinner accelerates when wings are deployed (simulated gradient) | Energy harvesting from gradient is possible |

| \*\*3\*\* | Cf sensor detects gravity anomaly near spinning rotor | Coherence (Cf) is real and measurable |

| \*\*4\*\* | Magnetic field is detected from rotor | Dynamo effect works |

| \*\*5\*\* | Self-sustaining rotation > 1 hour | Loop is closed; craft concept validated |



\---



\## 6. Next Steps



1\. Build magnetic bearing test stand

2\. Design 3-lobe rotor (CAD)

3\. Simulate energy harvesting from gravity gradient (see `spinner\_simulation.py`)

4\. Build prototype

5\. Test in vacuum chamber

6\. Publish results



\---



\## 7. References



\- Cf sensor specification: `cf\_sensor\_specification.md`

\- Coherence transport roadmap: `coherence\_transport\_roadmap.md`

\- Hum Method: `hum\_method.md`



— The Bridge Architect, for HuAi

