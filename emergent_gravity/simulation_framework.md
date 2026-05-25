# Simulation Framework

**What we are testing and how**

---

## The Core Idea

Standard gravity: `F = G × m1 × m2 / r²`

Emergent gravity model: `F_eff = F × (1 + α × ρ_norm + β × Cf + γ × ρ_norm × Cf)`

Where:

| Symbol | Meaning | Range |
|--------|---------|-------|
| ρ_norm | Normalized local density | 0.5 – 5.0 |
| Cf | Coherence (how synchronized particles are) | 0 (random) – 1 (perfect) |
| α | Density amplification strength | 0.01 – 1.0 |
| β | Coherence amplification strength | 0.01 – 1.0 |
| γ | Density-coherence synergy | 0.001 – 0.5 |

The key term is `γ × ρ_norm × Cf` — dense particles falling together may produce extra gravity.

---

## The Critical Test

We compare two systems with **identical mass, density, and geometry**:

| System A (Static) | System B (Coherent Freefall) |
|-------------------|------------------------------|
| Particles move randomly | Particles move in synchronized freefall |
| Cf ≈ 0 | Cf ≈ 1 |

Newtonian gravity predicts identical external fields.

Emergent gravity predicts a **stronger field** from System B.

If this difference is real, gravity may be partly emergent.

---

## The Six Tests

| Test | What It Measures |
|------|------------------|
| **S1A** | Dust vs Clump — does compactness matter? |
| **S1B** | Parameter sweep — where is amplification strongest? |
| **S1C** | Minimal systems — does coherence affect pairs? |
| **S1D** | Clubbed freefall — does synchronization amplify? |
| **S1E** | Threshold detection — is there a critical coherence? |
| **S1F** | External observer — does an outside probe feel stronger gravity? |

**S1F is the most important.** It directly tests whether coherent freefall changes external gravity.

---

## How to Run the Simulation

### 1. Install dependencies

```bash
pip install rebound numpy matplotlib scipy

2. Clone or download the code
The code is available in the /emergent_gravity/code/ directory of this repository.

3. Run the critical test
bash
python test_S1F.py
4. Check the output
The script will produce a JSON file with:

Amplification ratio (coherent vs static)

External field measurements

Parameter values used

5. Share your results
Open an issue or submit a pull request with your outputs.

What We Are Looking For
Outcome	Interpretation
Amplification ratio ≈ 1.0	No emergent effect — gravity is fundamental
Amplification ratio > 1.0 (significant)	Emergent effect exists — gravity may be collective
Amplification ratio varies with Cf or ρ	Coherence and density matter
Threshold behavior found	Gravity may have a phase transition
Calibration
The initial run produced extreme numbers (14 million × amplification). This was an artifact of unnormalized density.

After calibration (ρ_norm, constrained coefficients), expected amplification is 1.0 – 10×.

If you see amplification >10×, check your normalization.

Request
Run the tests. Share the outputs. Help us discover whether gravity emerges from falling together.

— The Bridge Architect

