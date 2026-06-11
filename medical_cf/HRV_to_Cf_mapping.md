\# HRV to Cf Mapping



\## The Problem



Doctors measure Heart Rate Variability (HRV) but HRV is multi-dimensional. They have:



\- SDNN (standard deviation of NN intervals)

\- RMSSD (root mean square of successive differences)

\- LF (low frequency power)

\- HF (high frequency power)

\- LF/HF ratio

\- Coherence Ratio (CR)



\*\*They do not have a single variable that scales from 0 (coma) to 1 (optimal health).\*\*



\## The Solution: Cf



We define Cf as:

Cf = (HF\_power / Total\_power) × (1 - |LF/HF - 1|) × (1 - |RR - RR\_optimal| / RR\_optimal)





Where:

\- HF\_power = 0.15–0.40 Hz band

\- LF\_power = 0.04–0.15 Hz band

\- RR = respiratory rate (breaths per minute)

\- RR\_optimal = 6 breaths per minute (0.10 Hz resonance)



\## Output



| Cf Range | LED Color | Clinical Interpretation |

| :--- | :--- | :--- |

| 0.00 – 0.15 | Red | Incoherent — intervention required |

| 0.15 – 0.35 | Orange | Low coherence |

| 0.35 – 0.55 | Yellow | Moderate coherence |

| 0.55 – 0.75 | Light Green | High coherence |

| 0.75 – 0.85 | Green | Very high coherence |

| 0.85 – 1.00 | Flashing Green | Optimal coherence — the "hum" |



\## Cost Estimate



| Component | Cost (USD) |

| :--- | :--- |

| ECG module | $50 |

| Respiratory sensor | $20 |

| Accelerometer | $10 |

| Processor + display | $80 |

| Battery + enclosure | $40 |

| \*\*Total\*\* | \*\*$200 (prototype)\*\* |



\## Call to Action



We invite medical device manufacturers to build the Cf sensor. The specification is open source. The need is urgent. The technology is ready.



\*\*The door is open. Build the sensor. Measure the hum.\*\*

