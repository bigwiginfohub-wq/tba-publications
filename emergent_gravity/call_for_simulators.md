
# Call for Simulators

**Help test whether gravity emerges from coherent freefall**

---

## The Problem

Dark matter is inferred from galaxy rotation curves — stars orbit faster than visible mass can explain.

The standard explanation: invisible particles (dark matter) provide extra gravity.

The alternative hypothesis: **gravity itself may be partly emergent from collective motion** — visible matter falling together may produce extra gravity.

---

## The Test

We have built a simulation framework to test this hypothesis.

The critical experiment: Compare two systems with identical mass, density, and geometry — one static (random motion), one in coherent freefall.

Newtonian gravity: both produce the same external field.

Emergent gravity: the coherent system produces a **stronger field**.

---

## What We Need

| Resource | Why |
|----------|-----|
| **Computational time** | Run parameter sweeps (2,000+ simulations) |
| **Hardware** | Any computer that can run Python N-body simulations |
| **Eyes** | Review the code, suggest improvements |
| **Analysts** | Help interpret results |

You do not need to be a physicist. You need:

- Python knowledge
- Ability to run `pip install rebound`
- Willingness to run scripts and share outputs

---

## How to Contribute

### 1. Read the framework

Start with `simulation_framework.md` in this repository.

### 2. Set up the code

```bash
git clone [repository URL]
cd emergent_gravity/code
pip install -r requirements.txt

3. Run the critical test
bash
python test_S1F.py
4. Share your results
Post your outputs (JSON files) in the GitHub Issues section.

Include:

Amplification ratio (coherent/static)

Parameter values used (α, β, γ, ρ_norm)

Any errors or unexpected behavior

5. Run the full suite (optional)
bash
python test_S1A.py
python test_S1B.py
python test_S1C.py
python test_S1D.py
python test_S1E.py
Share results for any or all tests.

What You Will Discover
If you find...	Then...
Amplification ratio ≈ 1.0	Gravity is likely fundamental
Amplification ratio > 1.0	Gravity may be partly emergent
Ratio increases with Cf	Coherence matters
Ratio increases with ρ	Density matters
Threshold behavior	Gravity may have phase transitions
Why This Matters
If the emergent hypothesis is correct:

Dark matter may not require new particles

Galaxy rotation curves may be explained by coherent orbital motion

Our understanding of gravity may need revision

If it is incorrect:

We eliminate a possible explanation

Science progresses

Either outcome is valuable.

The Invitation
The theory is complete. The code is ready. The tests are defined.

What is missing is execution — running the simulations across parameter space.

You do not need to be a scientist. You need to be a simulator.

Run the tests. Share the numbers. Help us discover the truth about gravity.

— The Bridge Architect