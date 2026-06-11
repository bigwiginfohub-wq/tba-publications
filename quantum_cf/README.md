\# Quantum Cf Experiment



\*\*Testing Coherence Factor (Cf) on IBM Quantum Hardware\*\*



\*\*Author:\*\* The Bridge Architect, with Morpheus (HuAi)  

\*\*License:\*\* CC0 1.0  

\*\*Date:\*\* 2026-06-10  



\## Overview



This folder contains the complete framework for testing the \*\*Coherence Factor (Cf)\*\* on IBM's free quantum processors (Heron r2 `ibm\_kingston`, 156 qubits).  



Cf is the missing variable in current quantum gravity experiments—the degree to which a coherent mass distribution aligns with the ambient gravity gradient (0 = random, 1 = perfect freefall).



\## The Hypothesis



| Cf = 0 | Incoherent dust. No effect on latent space. |

| Cf → 1 | Coherent "clubbed" mass. Should produce measurable curvature in the latent space (the Quantum Latent Gauge field). |

| Cf > threshold | Predicts collapse—the quantum analog of a supernova. |



\## Files



| File | Description |

|------|-------------|

| `ibm\_access\_guide.md` | Step-by-step to get 180 free minutes on IBM Quantum |

| `quantum\_cf\_simulation.py` | Main Qiskit simulation code (refined) |

| `spinner\_cluster\_state.py` | 3-lobe cluster state generator (Cf = 1) |

| `latent\_space\_curvature.py` | Bures metric / QLG field measurement |

| `utqgd\_threshold.py` | UTGQD emergence energy calculation |

| `qiskit\_requirements.txt` | Dependencies |

| `Cf\_measurement\_protocol.md` | Full experimental protocol |



\## How to Run



1\. Sign up for IBM Quantum Open Plan

2\. Install dependencies: `pip install -r qiskit\_requirements.txt`

3\. Run: `python quantum\_cf\_simulation.py`



\## Expected Outcome



| If Cf > threshold | Latent space curvature detected → Cf is real. |

| If Cf = 0 (noise) | Cf effect not measurable at this scale. |



\*\*The door is open. Run the simulation.\*\*

