# TRACEBIND: A Modular Framework for Survey Reconciliation and Kinematic Coherence

### Developed by The Bridge Architect

> "I have no formal training in astronomy and no institutional observatory behind me. What I had was curiosity, persistence, and a commitment to follow the evidence wherever it led. TRACEBIND was built on a simple principle: before searching for discoveries, reconcile the data. Before proposing explanations, measure the structure. Before claiming novelty, test whether the signal survives scrutiny."

---

## Why TRACEBIND Exists

Modern astronomy is built upon extraordinary surveys: Gaia, DESI, WISE, Pan-STARRS, SDSS, and many others. Each survey captures a different aspect of the sky, yet every catalog has limitations, selection effects, and incomplete overlap with the others.

**TRACEBIND** is a modular research framework consisting of independent but related analysis pipelines sharing common principles of validation, reproducibility, and cross-survey reconciliation. Its purpose is not to replace existing catalogs, nor to compete with large institutional pipelines. Its purpose is to systematically compare, validate, audit, and cross-reference information across surveys in order to identify overlooked candidates, quantify uncertainty, and reveal patterns that may otherwise remain hidden between datasets.

The philosophy is straightforward:

*   Reconcile before interpreting.
*   Validate before claiming.
*   Measure before explaining.

---

## Research Pillars

TRACEBIND is organized into three primary research themes:

### Pillar I: Survey Reconciliation & Extragalactic Isolation
The first application focuses on identifying high-confidence extragalactic candidates within Gaia DR3. The pipeline combines Gaia astrometric constraints, morphological indicators, infrared diagnostics, multi-survey cross-matching, and statistical filtering. A pilot analysis of ~12,500 sources successfully recovered a DESI-confirmed emission-line galaxy together with several high-priority AGN candidates.

### Pillar II: Astrometric Anomaly Ranking & Attribution
This theme focuses on identifying stars whose astrometric behavior is inconsistent with a single-star model. By engineering a composite `tension_score` from Gaia DR3 noise flags (RUWE and AEN), the framework ranks targets for unresolved companions. Validated against NSS catalogs, the tension score significantly enriches for binary solutions (Odds Ratio = 6.12) and retains independent predictive power beyond raw RUWE. Further hypothesis testing suggests unresolved multiplicity is a major contributor to high-tension anomalies.

### Pillar III: Kinematic Coherence Mapping
This theme introduces the **TRACEBIND-V11 Metric**, a quantitative observable for local position–velocity coherence. It measures the degree to which spatial proximity predicts velocity similarity beyond what is expected from local density and velocity dispersion alone. This is distinct from gravitational binding; bound clusters are always coherent, but coherent populations (e.g., tidal streams) are not necessarily bound.

---

## Validation Phases

The TRACEBIND-V11 Metric has undergone rigorous synthetic and real-data validation.

### Phase 1: Synthetic Signal Detection
Established that V11 reliably detects injected position–velocity coupling while rejecting geometry-only and isotropic null controls.

**Locked Configuration:**
```yaml
TRACEBIND_PHASE1_LOCK:
  dataset: synthetic_hyades_phase1_v2
  metric_version: V11_LOO
  k_predict: 30
  seed: 42
  validated_outputs:
    signal_ratio: 0.2033
    projection_control_ratio: 0.8154
```

### Phase 2: Robustness Envelope
Established operational boundaries under controlled degradation. The metric retains distributional separation under Gaussian noise (σ_plx ≤ 0.5 mas) and velocity dispersions up to 15 km/s. Sensitivity degradation is negligible (<1% ratio shift).

### Phase 3: Membership Contamination & Statistical Rigor
Tested resilience to realistic membership impurity. At 70% purity, separation was maintained in 2 of 3 Monte Carlo realizations, defining the **operational boundary for membership quality**. Established mandatory reporting standards: Wilson 95% CI, independent null RNG streams, and effect size reporting.

### Phase 4: Real Gaia DR3 Hyades Application & Methodological Characterization

#### 4A: Implementation Stability & Control Refinement
Across multiple independent implementations (V3–V6) and code refactoring, the Hyades median ratio remained remarkably stable at **R = 0.849 ± 0.005**. Field medians consistently cluster around 0.98–0.99. Stratified magnitude matching reduced G-mag KS statistic from ~0.37 to **0.064**, eliminating observational bias as a confounding factor. Single Gaia query + local bootstrapping ensures reproducibility and isolates sampling variance.

#### 4B: Benchmark Reproduction
The Hyades baseline was successfully reproduced using the generic `run_benchmark.py` framework:
-   Cluster Median: **0.8499 ± 0.0039** (consistent with V6)
-   Separation Frequency: **10%** (within expected bootstrap variance)
-   G-mag KS: **0.065** (consistent with V6)

**Conclusion:** The TRACEBIND signal is stable across independent code paths. Variability in separation frequency is a property of control population sampling, not metric implementation.

#### 4C: Primary Observable vs. Separation Diagnostic
Formal Q₉₇.₅/Q₂.₅ separation frequency fluctuates between 6–12% across runs. This reflects inherent sensitivity of extreme percentiles to sampling noise rather than metric instability. Mann-Whitney U test (p < 10⁻⁶³) confirms substantial distributional shifts even when tail separation fails. **Median ratio R is the primary stable observable; separation frequency is a secondary diagnostic.**

#### 4D: Contamination Calibration
Simulated contamination demonstrates systematic response: R transitions from ~0.85 toward field baselines (~0.99) as purity decreases. Separation frequency declines monotonically beyond 20% contamination, defining operational envelope. Observed Hyades value aligns with low-contamination regime.

**Boundary Statement:** These simulations indicate TRACEBIND V11 responds systematically to controlled degradation of membership purity. It does NOT yet function as a calibrated purity estimator for arbitrary populations, as response depends on specific field population, contamination model, and cluster kinematics used in these experiments.

#### 4E: Spatial Selection Sensitivity & Core Property Verification (Pleiades Region)
Applied identical frozen V11 pipeline to broad spatial selection in Pleiades direction using independent Gaia Archive ADQL cross-validation:

**Initial Broad Selection (8° Radius):**
-   N = 7,134 sources | Median Distance = 151.6 pc | Median Parallax = 6.60 mas
-   Discrepancy from literature (~136 pc) attributed to field star contamination passing quality cuts but lacking membership probability filtering.

**Core-Dominated Selection (4° Radius):**
-   N = 2,665 sources | Median Distance = 139.3 pc | Median Parallax = 7.18 mas
-   Residual ~2% distance offset is consistent with expected field-star fraction at this galactic latitude; provides strong evidence that the adopted coordinates and quality-selection pipeline are functioning as intended.

**Vetted Membership Requirement:**
Even the 4° core sample retains ~30–40% field contamination without explicit Pmem ≥ 0.9 filtering. Observed Hyades median R = 0.849 remains the only valid benchmark for intrinsic coherence claims.

**Pleiades DR3 Benchmark Construction (Completed):**
We cross-matched 810 high-probability CG22 members to Gaia DR3 using the official `gaiaedr3.dr2_neighbourhood` table. One mapped source (DR3 ID `66828870787370624`) lacked a published astrometric solution (parallax, proper motion, and RUWE were unavailable) and was automatically excluded. The remaining 749 sources passed all TRACEBIND quality criteria (RUWE < 1.4, G < 18, plx_sn > 10) and constitute the final analysis sample. The median distance of this sample is 135.81 pc, representing a −0.41 pc shift from the DR2 baseline, consistent with inter-release systematics.

**Boundary Statement:**  
Spatial or kinematic selections WITHOUT vetted membership catalogs produce predictable, quantifiable bias due to field-star contamination. This bias is expected physics, not a pipeline error. Only high-purity, independently curated membership samples (e.g., CG22 Pmem ≥ 0.9) are valid for external generalization tests. The Pleiades DR3 benchmark is now ready for V11 coherence testing against the locked Hyades baseline.

**Frozen Baseline for Generalization:**  
Hyades Median R = 0.849 ± 0.005 | Field R ≈ 0.985 | Sep. Freq ≈ 8%.  
All future validation experiments must be compared against this locked reference.

#### 4G: Neighborhood Size (k) Sensitivity Analysis
Tested robustness of Hyades coherence signal across K_PREDICT ∈ {20, 25, 30, 35, 40} with K_SHUFFLE fixed at 50 and identical cluster/field samples held constant.

**Primary Observable Stability:**  
Cluster median ratio varies only 0.8276 → 0.8590 (range = 0.031, CV = 0.4%) across all tested k values. Field median remains extremely stable at 0.980 ± 0.003 regardless of k. This confirms the central tendency of the TRACEBIND V11 observable is reasonably insensitive to moderate changes in neighborhood size.

**Separation Criterion Sensitivity:**  
Formal Q₇.₅/Q₂.₅ separation frequency increases substantially at larger k: 0% (k=20–30) → 10% (k=35) → 55% (k=40). This reflects expected tail sensitivity: while medians remain stable, extreme quantiles shift sufficiently to alter overlap. The separation criterion is therefore more sensitive to k than the underlying observable itself.

**Boundary Statement:**  
These results do NOT establish k=40 as optimal. Larger neighborhoods may improve separation for Hyades specifically but could degrade performance for clusters with different spatial densities or velocity dispersions. k=30 remains the frozen baseline for generalization testing; future work must evaluate k-dependence on independently vetted clusters before any parameter tuning claims can be made.

---

## What TRACEBIND Has Demonstrated

### Established
*   Reproducible multi-survey reconciliation can recover externally validated astrophysical targets.
*   The $C_f$ statistic is analytically equivalent to the Mean Resultant Length.
*   The composite astrometric tension metric significantly enriches for Gaia DR3 Non-Single Star solutions.
*   High-tension stars are significantly enriched in known binary systems (WDS/SB9).
*   The V11 LOO metric reliably detects injected position-velocity coupling in synthetic data.
*   The metric tolerates kinematic contamination down to ~70% purity.
*   Real Gaia DR3 Hyades members show statistically significant position-velocity structure relative to matched field stars.
*   **Implementation Stability:** Hyades median ratio = 0.849 ± 0.005 (stable across V3–V6 and benchmark reproduction).
*   **Contamination Response:** Metric degrades gracefully toward field baseline as purity decreases, with separation frequency declining monotonically beyond 20% contamination.
*   **Sample Definition Sensitivity:** Broad spatial selections yield intermediate ratios between vetted clusters and field, consistent with sensitivity to membership purity
*   **Reproducible DR2→DR3 Benchmarking:** Successfully mapped 810 CG22 Pleiades members to Gaia DR3 via the official neighbour table, documenting one astrometric anomaly and producing a fully audited 749-star analysis sample.

### Not Established
TRACEBIND does not currently demonstrate:
*   Discovery of new stellar streams or moving groups.
*   Definitive discovery of specific exoplanets or companion masses based solely on astrometric tension.
*   Evidence for or against dark matter, MOND, or alternative gravity theories.
*   Clean $Q_{97.5}/Q_{2.5}$ separation in real Gaia DR3 data (only statistical significance achieved).
*   Robustness to full Gaia DR3 covariance, scan-law systematics, or spatial contamination.
*   Causal position-velocity coupling in any real stellar population.
*   Calibrated purity estimation for arbitrary populations.

Such claims require additional phase-space analysis, radial velocities, Proper Motion Anomaly (PMa) calculations, full covariance propagation, literature-grade membership catalogs, and independent validation on multiple vetted clusters.

---

## The Philosophy of Anomaly Prioritization

TRACEBIND does not attempt to replace astrophysical theory. Its purpose is to systematically identify where survey descriptions, catalog assumptions, and physical interpretations begin to diverge from observations. In this sense, TRACEBIND functions as a scientific stress-testing framework for astronomical catalogs and models.

Rather than searching directly for planets, binaries, AGN, stellar streams, or other phenomena, TRACEBIND identifies populations whose observed properties deserve further scrutiny and then evaluates competing physical explanations through independent datasets.

The framework is designed to move systematically through four stages:
1.  Detection of tension
2.  Validation of tension
3.  Physical attribution of tension
4.  Follow-up prioritization

Scientific progress often begins not with answers, but with careful observation. The role of TRACEBIND is to create conditions under which meaningful patterns can emerge from the data and then be tested rigorously.


```
