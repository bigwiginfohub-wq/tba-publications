
# TRACEBIND: Survey Reconciliation, Kinematic Mapping, and Astrometric Anomaly Attribution

### Developed by The Bridge Architect

> "I have no formal training in astronomy and no institutional observatory behind me. What I had was curiosity, persistence, and a commitment to follow the evidence wherever it led. TRACEBIND was built on a simple principle: before searching for discoveries, reconcile the data. Before proposing explanations, measure the structure. Before claiming novelty, test whether the signal survives scrutiny."

---

## Why TRACEBIND Exists

Modern astronomy is built upon extraordinary surveys: Gaia, DESI, WISE, Pan-STARRS, SDSS, and many others. Each survey captures a different aspect of the sky, yet every catalog has limitations, selection effects, and incomplete overlap with the others.

TRACEBIND was created as a reconciliation framework.

Its purpose is not to replace existing catalogs, nor to compete with large institutional pipelines. Its purpose is to systematically compare, validate, audit, and cross-reference information across surveys in order to identify overlooked candidates, quantify uncertainty, and reveal patterns that may otherwise remain hidden between datasets.

The philosophy is straightforward:

-   Reconcile before interpreting.
-   Validate before claiming.
-   Measure before explaining.

---

## Pillar I: Extragalactic Candidate Isolation

The first application of TRACEBIND focuses on identifying high-confidence extragalactic candidates within Gaia DR3.

The pipeline combines Gaia astrometric constraints, morphological indicators, infrared diagnostics, multi-survey cross-matching, and statistical filtering. The objective is not to declare discoveries, but to construct reproducible candidate lists for follow-up investigation.

A pilot analysis of approximately 12,500 sources produced a validated DESI-confirmed emission-line galaxy recovery case, several high-priority infrared-selected AGN candidates, and a fully documented filtering workflow.

---

## Pillar II: Directional Coherence and Galactic Kinematics

TRACEBIND was later extended to study large-scale proper-motion structure within Gaia data.

This work introduced the directional coherence statistic ($C_f$), which was subsequently shown to be analytically equivalent to the Mean Resultant Length ($R$), a standard quantity in directional statistics. Using Gaia proper motions, TRACEBIND computes localized coherence fields across the sky and evaluates them through bootstrap uncertainty estimation, Monte Carlo null models, permutation testing, and Galactic-background subtraction.

Analyses indicate that Gaia proper-motion fields exhibit coherence significantly above randomized expectations, and that residual coherence remains statistically significant after subtraction of first-order Galactic rotation and solar reflex motion.

---

## Pillar III: Astrometric Anomaly Ranking

The evolution of TRACEBIND into the local solar neighborhood focuses on identifying stars whose astrometric behavior is inconsistent with a single-star model.

By engineering a composite `tension_score` from Gaia DR3 astrometric noise flags (RUWE and Astrometric Excess Noise), the framework ranks targets for unresolved companions. Instead of treating noise flags as binary vetoes, TRACEBIND uses logarithmic compression to capture the heavy-tail of astrometric model failures.

Validated against the Gaia DR3 Non-Single Star (NSS) catalogs, the tension score significantly enriches for NSS solutions (Odds Ratio = 6.12, $p = 9.44 \times 10^{-6}$) and retains independent predictive power beyond raw RUWE and excess noise (Logistic Regression Pseudo-R² increases from 0.16 to 0.31).

---

## Pillar IV: Physical-Origin Testing of Astrometric Anomalies

Astrometric anomalies can arise from multiple physical mechanisms, including unresolved stellar companions, brown dwarfs, giant planets, stellar activity, rotational spot modulation, or catalog systematics.

TRACEBIND Phase 12 extends anomaly ranking into hypothesis testing by comparing high-tension stars against matched control populations. The objective is not merely to identify anomalies, but to determine which physical mechanisms most plausibly generate them.

Current investigations include:
-   GALEX ultraviolet activity diagnostics
-   TESS photometric variability indicators
-   Known multiplicity catalogs (WDS, SB9)

Initial results indicate:
-   No statistically significant enhancement in UV activity relative to matched controls.
-   No enrichment in cataloged optical variability flags.
-   Significant enrichment in known binary systems (Odds Ratio ≈ 4.03, p = 0.0095).

These findings suggest unresolved multiplicity is a major contributor to the highest TRACEBIND astrometric tensions. Further validation remains ongoing.

---

## Pillar V: Phase 1 Validation — Synthetic Signal Detection

TRACEBIND Phase 1 established that the V11 metric can reliably detect injected position–velocity coupling in synthetic data while rejecting geometry-only and isotropic null controls. This validates the metric's discriminative power under controlled conditions, but does not establish causal binding in real astronomical populations.

### Validated Claim (Phase 1)

> The TRACEBIND V11 metric detects injected position–velocity structure in synthetic signal populations while correctly rejecting designed null populations that preserve spatial geometry or velocity distributions without injected position–velocity coupling.

Causal language ("true P(v|x) coupling") is reserved for real-data validation with proper error propagation and contamination modeling.

### Locked Experimental Configuration (Regression Test)

All future metric modifications **must** reproduce the population ordering invariant on the locked dataset before being considered valid. Any change that breaks this invariant is rejected.

```yaml
TRACEBIND_PHASE1_LOCK:
  dataset: synthetic_hyades_phase1_v2
  generator_version: V2.0  # Corrected projection null; parallax NOT shuffled
  metric_version: V11_LOO  # Non-degenerate leave-one-out prediction
  k_predict: 30
  k_shuffle: 50
  permutations: 50
  seed: 42
  threshold_signal_max_ratio: 0.80
  threshold_control_min_ratio: 0.80

  validated_outputs:
    signal_ratio: 0.2033
    projection_control_ratio: 0.8154
    field_control_ratio: 0.8563

  acceptance:
    must_preserve_population_order:
      - signal_ratio < projection_control_ratio
      - signal_ratio < field_control_ratio
```

### Key Fixes That Enabled Validation

-   **Removed predictor degeneracy:** Original residual predictor collapsed algebraically (`pred_res ≈ 0`). Fixed via LOO prediction excluding self.
-   **Removed baseline contamination:** Replaced shared null normalization with per-population local-shuffle baselines.
-   **Fixed projection null failure:** Original generator preserved velocity direction coherence (cosine ≈ 0.998). Corrected via isotropic PM-direction randomization (RA/Dec shuffled; parallax not shuffled in V2.0).
-   **Fixed audit metric:** Replaced degenerate Pearson correlation on 2-element vectors with cosine similarity for directional alignment.

### Phase 1 Boundary (What Is NOT Proven)

-   ❌ Causal position–velocity coupling in real stars
-   ❌ Robustness to Gaia measurement uncertainties
-   ❌ Performance under field contamination (>10%)
-   ❌ Sensitivity to weak signals (σ > 1.5 km/s)
-   ❌ Applicability beyond synthetic Hyades-like clusters

These are exclusively Phase 2+ concerns.

---

## Pillar VI: Phase 2 Validation — Robustness Envelope

TRACEBIND Phase 2 established the operational boundaries of the V11 metric under controlled degradation. All tests used the locked V11 LOO predictor with per-population local-shuffle baselines.

### Validated Performance Envelope

| Stress Dimension         | Tested Range                          | Outcome              | Key Finding                                               |
| :----------------------- | :------------------------------------ | :------------------- | :-------------------------------------------------------- |
| Signal Strength (σ)      | 1.5 – 15.0 km/s                       | ✅ Separation maintained | Margin degrades smoothly from +0.76 to +0.15; no cliff    |
| Seed Reproducibility     | Seeds {1, 42, 123, 999}               | ✅ Ordering preserved    | Field margin min = +0.016; no ordering violations         |
| Distributional Separation| 95% NRI non-overlap                   | ✅ Fully separated       | Signal NRI upper < Control NRI lower at all tested σ      |
| Gaussian Obs. Noise      | σ_plx ≤ 0.5 mas, σ_pm ≤ 1.0 mas/yr   | ✅ All 90 conditions pass | ΔSig < 0.006; PM errors dominate over parallax            |

### Scientific Claim Boundary

> Under independent Gaussian observational noise spanning Gaia-like error amplitudes, and for intrinsic velocity dispersions up to 15 km/s, the V11 metric retains distributional separation between injected convergent structure and geometry-only/isotropic null controls. Sensitivity degradation is negligible (<1% ratio shift) across the tested noise range.

This does NOT establish robustness to full Gaia DR3 systematics (covariance, scan-law, magnitude/color dependence, crowding, binaries). Those remain Phase 3+ requirements.

### Formal Separation Criterion

Distributional separation between signal and control populations is defined as:

$$Q_{97.5}(R_{\text{signal}}) < Q_{2.5}(R_{\text{control}})$$

where $R = E_{\text{real}} / E_{\text{null},i}$ is the prediction-error ratio distribution computed over $N_{\text{perm}}$ local-shuffle null realizations, and $Q_p$ denotes the $p$-th percentile. This criterion requires complete non-overlap of the central 95% null-ratio intervals and is applied identically across all validation phases.

### Locked Configuration

All Phase 2 results are reproducible via `phase2_signal_sweep.py`, `phase2_robustness_audit.py`, `phase2_statistical_margin.py`, and `phase2d_measurement_noise.py` with seed=42 and parameters as documented in each script header.

---

## Pillar VII: Phase 3 Validation — Membership Contamination & Statistical Rigor

TRACEBIND Phase 3 tested the metric’s resilience to realistic membership impurity and established publication-grade statistical reporting standards. This phase bridges synthetic validation and real-data application.

### Kinematic Contamination Robustness

Using the locked V2.0 generator with deterministic RNG streams, the metric was tested under kinematic-only contamination (spatial coordinates preserved, PMs replaced with field values):

| Purity | Signal Median | Projection Median | Field Median | Separation Maintained |
| :----- | :------------ | :---------------- | :----------- | :-------------------- |
| 100%   | 0.207         | 0.960             | 0.811        | ✅ Yes                 |
| 90%    | 0.244         | 1.002             | 0.858        | ✅ Yes                 |
| 80%    | 0.311         | 0.962             | 0.836        | ✅ Yes                 |
| 70%    | 0.385         | 0.997             | 0.841        | ⚠️ Near limit (2/3 seeds) |

At 70% purity, separation was maintained in 2 of 3 Monte Carlo realizations, defining the **operational boundary for membership quality**. Below this threshold, the metric cannot reliably distinguish signal from contaminated field.

### Statistical Reporting Standard

Phase 3 established mandatory reporting requirements for all subsequent analyses:
-   **Wilson 95% CI** for all binomial success rates (replacing point estimates)
-   **Independent null RNG streams** per population (no shared state)
-   **Effect size reporting** alongside p-values
-   **No qualitative labels** ("robust"/"failed") without quantitative support

### Phase 3 Boundary

-   ❌ Full Gaia DR3 covariance propagation not yet implemented
-   ❌ Spatial contamination (position corruption) not yet tested
-   ❌ Real-data membership probabilities not yet incorporated

---

## Pillar VIII: Real Gaia DR3 Hyades Application

### Result

Statistically significant detection (Mann-Whitney U $p = 1.67 \times 10^{-22}$, effect size $r = 0.220$) but formal $Q_{97.5}/Q_{2.5}$ separation **NOT achieved**.

### Interpretation

TRACEBIND detects real position-velocity structure in Hyades members. Overlap with field distribution is attributed to:
1.  Residual contamination in astrometric-only membership selection (no literature membership probabilities)
2.  Absence of full 5D covariance propagation in distance/PM conversion
3.  Possible non-member interlopers passing RUWE/G-mag cuts

### Operational Boundary Defined

Under Gaia DR3 astrometric selection alone (no literature membership probabilities, no covariance), the metric distinguishes Hyades from field at high significance but does not achieve clean distributional separation per the formal criterion.

### Locked Baseline

| Population | Median Ratio | Notes                     |
| :--------- | :----------- | :------------------------ |
| Hyades     | 0.8492       | Astrometric-only selection |
| Field      | 0.9075       | Matched G-mag, excluded zone |

All future real-data improvements (better membership, covariance propagation, spatial contamination testing) must exceed this baseline to demonstrate progress.

---

## What TRACEBIND Has Demonstrated

### Established

-   Reproducible multi-survey reconciliation can recover externally validated astrophysical targets.
-   The $C_f$ statistic is analytically equivalent to the Mean Resultant Length.
-   Gaia proper-motion fields contain statistically significant directional coherence.
-   Residual coherence persists after first-order Galactic-background subtraction.
-   The composite astrometric tension metric significantly enriches for Gaia DR3 Non-Single Star solutions and provides independent predictive value.
-   High-tension stars show no statistically significant UV activity enhancement relative to matched controls.
-   High-tension stars show no enrichment in cataloged TIC variability flags.
-   High-tension stars are significantly enriched in known binary systems (WDS/SB9).
-   The V11 LOO metric reliably detects injected position-velocity coupling in synthetic data while rejecting geometry-only and isotropic nulls.
-   The metric maintains separation under Gaussian noise (σ_plx ≤ 0.5 mas, σ_pm ≤ 1.0 mas/yr) and velocity dispersions up to 15 km/s.
-   The metric tolerates kinematic contamination down to ~70% purity before separation degrades.
-   Real Gaia DR3 Hyades members show statistically significant position-velocity structure relative to matched field stars.

### Not Established

TRACEBIND does not currently demonstrate:

-   Discovery of new stellar streams or moving groups.
-   Definitive discovery of specific exoplanets, brown dwarfs, or companion masses based solely on astrometric tension.
-   Evidence for or against dark matter, MOND, or alternative gravity theories.
-   Identification of previously unknown Galactic substructures.
-   Clean $Q_{97.5}/Q_{2.5}$ separation in real Gaia DR3 data (only statistical significance achieved).
-   Robustness to full Gaia DR3 covariance, scan-law systematics, or spatial contamination.
-   Causal position-velocity coupling in any real stellar population.

Such claims require additional phase-space analysis, radial velocities, Proper Motion Anomaly (PMa) calculations, full covariance propagation, literature-grade membership catalogs, and independent validation.

---

### What TRACEBIND Measures

TRACEBIND quantifies **local kinematic coherence**: the degree to which 
spatial proximity predicts velocity similarity beyond what is expected 
from local density and velocity dispersion alone.

This is distinct from gravitational binding. Bound clusters are always 
coherent, but coherent populations are not necessarily bound (e.g., 
dissolving associations, tidal streams). TRACEBIND is a detector of 
shared phase-space structure; dynamical interpretation requires 
supplementary evidence.

## The Philosophy of Anomaly Prioritization

TRACEBIND does not attempt to replace astrophysical theory.

Its purpose is to systematically identify where survey descriptions, catalog assumptions, and physical interpretations begin to diverge from observations. In this sense, TRACEBIND functions as a scientific stress-testing framework for astronomical catalogs and models.

Rather than searching directly for planets, binaries, AGN, stellar streams, or other phenomena, TRACEBIND identifies populations whose observed properties deserve further scrutiny and then evaluates competing physical explanations through independent datasets.

The framework is designed to move systematically through four stages:

1.  Detection of tension
2.  Validation of tension
3.  Physical attribution of tension
4.  Follow-up prioritization

Scientific progress often begins not with answers, but with careful observation. The role of TRACEBIND is to create conditions under which meaningful patterns can emerge from the data and then be tested rigorously.

The sky does not belong to any pipeline. The measurements belong to the surveys. The interpretations belong to the evidence. TRACEBIND exists to help connect the two.
