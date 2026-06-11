\# Cf Measurement Protocol



\## Objective

Measure the Coherence Factor (Cf) using IBM's Heron r2 processor (`ibm\_kingston`) and detect latent space curvature.



\## Protocol Steps



| Step | Action | Duration |

|------|--------|----------|

| 1 | Connect to `ibm\_kingston` | 1 min |

| 2 | Run baseline (Cf = 0) | 2 min |

| 3 | Run Cf sweep (0.25, 0.5, 0.75, 0.85, 0.95, 0.999) | 15 min |

| 4 | Calculate latent curvature (κ) from results | 1 min |

| 5 | Compare with UTGQD threshold (κ > 0.01) | 1 min |



\## Success Criteria



| κ < 0.01 | No curvature → Cf not measurable |

| κ > 0.01 | Curvature detected → Cf is real |

| κ > 0.1 | Strong curvature → QLG field active |



\## Falsification

If κ does not increase with Cf, the hypothesis is falsified.



\*\*The door is open. Run the protocol.\*\*

