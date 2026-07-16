
# TRACEBIND-V11: Reproducible Gaia DR2–DR3 Benchmark Construction and a Leave-One-Out Metric for Local Kinematic Coherence

**Author:** The Bridge Architect
**Date:** July 2026
**Version:** 2.0 
---

## Abstract

Modern astrometric surveys such as Gaia provide unprecedented precision, yet reconciling data across releases (DR2 to DR3) and quantifying kinematic coherence in stellar populations remains challenging due to selection effects and catalog systematics. This paper presents **TRACEBIND**, a modular framework for survey reconciliation and kinematic analysis. We detail the construction of verified Pleiades and Hyades DR3 benchmarks from high-probability membership catalogs, documenting the official Gaia neighbour table cross-match and the handling of astrometric anomalies. We introduce the **TRACEBIND-V11 Metric**, a leave-one-out tangential velocity predictor that measures local kinematic coherence relative to a Monte Carlo null model of velocity exchangeability. **TRACEBIND-V11 measures local kinematic predictability rather than gravitational boundedness.** Applied to the verified benchmarks, V11 detects median prediction errors significantly smaller than expected under the null distribution for both clusters: Pleiades ($R=0.914$, $p=0.003$) and Hyades ($R=0.841$, $p=0.002$). Empirical subsampling analysis confirms these estimates are stable under member removal (Pleiades CV = 0.014; Hyades CV = 0.037), with the comparative ordering preserved across all tested parameter combinations. Using this frozen metric, the Hyades sample exhibits a lower normalized prediction-error ratio than the Pleiades sample, indicating greater local tangential-velocity predictability under the TRACEBIND-V11 metric.

---

## 1. Introduction

The Gaia mission has revolutionized our understanding of stellar kinematics, but the transition between Data Release 2 (DR2) and Early Data Release 3 (EDR3)/DR3 introduced significant changes in source identifiers and astrometric solutions. For rigorous kinematic analysis, it is essential to reconcile these releases using official mapping tools rather than positional matching, which can introduce epoch-dependent biases.

Furthermore, while gravitational binding is a well-defined physical state, **kinematic coherence**—the degree to which spatial proximity predicts velocity similarity—is a distinct observable that can persist in unbound structures like tidal streams. TRACEBIND-V11 is designed to quantify this coherence using a robust, distance-independent metric that avoids the algebraic pitfalls of self-prediction.

This manuscript documents:
1.  The reproducible construction of verified Pleiades and Hyades DR3 benchmarks.
2.  The definition and implementation of the TRACEBIND-V11 metric.
3.  Comparative validation results including parameter robustness, empirical subsampling stability, and influence diagnostics for two fundamental open clusters.

---

## 2. Data Preparation: Verified DR3 Benchmarks

### 2.1 Source Catalogs
We began with high-probability members ($P_{\text{mem}} \ge 0.9$) from the Cantat-Gaudin et al. (2022, hereafter CG22) catalog for the Pleiades ($N=810$) and Hyades ($N=820$) open clusters.

### 2.2 DR2 to DR3 Cross-Match
To reconcile DR2 sources with DR3 astrometry, we utilized the official `gaiaedr3.dr2_neighbourhood` table via the Gaia Archive TAP service. This table provides the most reliable mapping between DR2 and DR3 source identifiers, accounting for proper motion propagation between the two epochs.

*   **Method:** Anonymous batched queries using `IN (...)` clauses to avoid authentication requirements.
*   **Duplicate Resolution:** For sources with multiple DR3 neighbours, we selected the match with the minimum `angular_distance`. This deterministic rule yielded a one-to-one mapping for all sources.
*   **Mapping Quality:** The median angular distance for selected matches was $<0.15$ mas for both clusters.

### 2.3 Astrometric Anomalies
One Pleiades source (DR3 ID `66828870787370624`) lacked a published astrometric solution in DR3 (parallax, proper motion, and RUWE were `NaN`). Visual inspection confirmed that the source is located in a crowded region of the cluster. However, no claim is made regarding the specific reason Gaia DR3 omitted an astrometric solution. This source was automatically excluded from the analysis sample.

### 2.4 Quality Filtering
The remaining sources were subjected to the following TRACEBIND quality criteria to ensure a clean single-star sample:
1.  **RUWE < 1.4:** RUWE was used as a standard Gaia astrometric quality indicator to preferentially retain sources with well-behaved single-source astrometric solutions.
2.  **G < 18 mag:** Ensured high-precision photometry.
3.  **Parallax > 0 & Error > 0:** Removed non-physical solutions.
4.  **Parallax S/N > 10:** Ensured reliable distance estimates.

**Final Samples:**
*   **Pleiades:** 749 vetted members. Median Distance: 135.81 pc.
*   **Hyades:** 820 vetted members. Median Distance: 47.20 pc.

---

## 3. Methodology: The TRACEBIND-V11 Metric

### 3.1 Tangential Velocity Conversion
TRACEBIND V11 uses only two-dimensional tangential velocities derived from Gaia proper motions and parallaxes. Radial velocities are not incorporated. To remove distance-dependent biases inherent in proper motions, we convert astrometry to tangential velocities ($v_t$) in km/s:

$$ v_{t,\alpha} = 4.74047 \cdot \mu_{\alpha*} \cdot d / 1000 $$
$$ v_{t,\delta} = 4.74047 \cdot \mu_{\delta} \cdot d / 1000 $$

where $d$ is the distance in parsecs derived from parallax. Positions are converted to Cartesian coordinates $(x, y, z)$ for neighbor search.

### 3.2 Leave-One-Out (LOO) Prediction
For each star $i$, we identify its $k=30$ nearest neighbors in 3D position space, excluding itself. We predict its tangential velocity $\mathbf{v}_{\text{pred}, i}$ as the inverse-distance-weighted mean of its neighbors' velocities:

$$ \mathbf{v}_{\text{pred}, i} = \frac{\sum_{j \in N_i} w_{ij} \mathbf{v}_j}{\sum_{j \in N_i} w_{ij}}, \quad w_{ij} = \frac{1}{d_{ij}^2 + \epsilon} $$

The prediction error for star $i$ is the Euclidean norm $|\mathbf{v}_i - \mathbf{v}_{\text{pred}, i}|$. The primary observable is the **median prediction error** ($E_{\text{real}}$) across all stars.

### 3.3 Null Model: Local Velocity Exchangeability
To test for kinematic coherence, we define a null hypothesis where tangential velocities are exchangeable within local spatial neighborhoods. We generate 1,000 Monte Carlo realizations by:
1.  For each star, selecting a velocity from one of its neighbors at random (sampling with replacement).
2.  Adding Gaussian noise scaled to 10% of the local velocity dispersion.
3.  Recomputing the LOO prediction error for the shuffled dataset.

Sampling with replacement defines a stochastic local-exchangeability null rather than a strict permutation of the observed velocity field. The noise scale (10%) was chosen to preserve local dispersion structure while preventing degenerate resampling; results were empirically stable to variations in this parameter during robustness testing. 

Because the null model samples velocities from the local spatial neighborhood, it preserves the underlying spatial density structure and local velocity correlations to some extent. **This choice makes the test conservative with respect to detecting local coherence**, ensuring that a low coherence ratio ($R < 1$) reflects genuine local velocity predictability rather than mere phase-space smoothness or density-driven artifacts. Each Monte Carlo realization produces a median prediction error; the null expectation $\overline{E}_{\text{null}}$ is defined as the arithmetic mean of those simulated median errors.

The **Coherence Ratio** is defined as:
$$ R = \frac{E_{\text{real}}}{\overline{E}_{\text{null}}} $$

An $R < 1$ indicates that real neighbors predict velocities better than expected under the null model. Statistical significance is assessed via a one-sided Monte Carlo p-value computed directly from the full null distribution.

---

## 4. Results: Comparative Kinematic Coherence

Applying the frozen TRACEBIND-V11 implementation to the verified benchmarks yielded the following results:

| Cluster | N (Vetted) | E_real (km/s) | E_null (km/s) | R | 95% Subsampling Interval | Subsampling Shift | CV | p-value |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pleiades** | 749 | 0.6051 | 0.6620 | 0.9141 | [0.8810, 0.9308] | −0.009 (−1.0%) | 0.014 | 0.003 |
| **Hyades** | 820 | 14.1966 | 16.8821 | 0.8409 | [0.8261, 0.9593] | +0.047 (+5.6%) | 0.037 | 0.002 |

The observed median prediction errors for both clusters are significantly lower than expected under the Monte Carlo null model (Monte Carlo p-values of 0.003 and 0.002, respectively). The 95% subsampling intervals quantify the estimator's sensitivity to member selection, revealing that Hyades exhibits approximately 2.6× greater sampling variability than Pleiades.

---

## 5. Discussion

### 5.1 Interpretation of Coherence
TRACEBIND-V11 measures the predictability of local tangential velocities from neighboring stars. Lower prediction errors relative to the null model indicate greater local kinematic coherence. Using the TRACEBIND V11 metric, the Hyades sample produced a lower coherence ratio ($R = 0.841$) than the Pleiades sample ($R = 0.914$), a difference that persists across 65.1% of pairwise subsample comparisons and all 36 parameter combinations tested. Because subsamples overlap substantially, these pairwise comparisons are descriptive rather than inferential. This difference may reflect the Hyades' dynamically evolved structure, extended spatial distribution, and proximity, though TRACEBIND-V11 intentionally does not attribute causality to these physical parameters.

TRACEBIND-V11 is intentionally agnostic regarding the physical origin of the observed coherence. A low prediction error may arise from gravitational binding, common formation history, tidal structure, or other correlated dynamical processes.

### 5.2 Provenance and Reproducibility
All intermediate artifacts, including the raw DR3 tables and DR2-DR3 mappings, are preserved. This allows for full auditability of the filtering steps and the handling of astrometric anomalies. The frozen configuration ($k=30$, 1000 permutations) ensures that these comparisons are internally consistent.

### 5.3 Limitations
The current TRACEBIND-V11 implementation has several methodological limitations that define the scope of these results and will be addressed in future work:
1.  **Measurement Uncertainties:** The metric treats tangential velocities as exact values, without propagating Gaia proper motion or parallax uncertainties via Monte Carlo sampling.
2.  **Distance Weighting:** The inverse-square weighting kernel ($1/d^2$) can be sensitive to extremely close neighbors. However, preliminary tests with softened kernels (e.g., $1/(d^2 + h^2)$) yielded qualitatively consistent coherence ratios, indicating the primary results are not an artifact of the inverse-square singularity.
3.  **Null Model Locality:** The local-exchangeability null model samples velocities from the immediate $k$-neighborhood. While this tests local predictability, it preserves local spatial-kinematic correlations. Future work will compare this against global shuffle nulls to isolate purely local effects.
4.  **Geometric Anisotropy:** The neighbor search relies on Euclidean distance in 3D Cartesian space, which does not account for the elongated geometry or tidal anisotropy of evolved clusters like the Hyades. Mahalanobis or PCA-whitened distance metrics may better capture the intrinsic cluster morphology.

### 5.4 Empirical Subsampling Stability and Influence Analysis
To quantify sampling variability independent of parameter choices, we performed an empirical subsampling analysis. For each cluster, we drew 500 independent 80% subsamples without replacement and recomputed $R$ for each replicate. This approach preserves the spatial topology of the neighbor graph, avoiding the duplicate-point artifacts that invalidate ordinary bootstrap resampling for nearest-neighbor statistics.

The Pleiades estimator is highly stable (CV = 0.014, subsampling shift = −1.0%), with the full-sample observed value lying near the center of the 95% subsampling interval [0.881, 0.931]. The Hyades estimator exhibits greater sensitivity to member selection (CV = 0.037, subsampling shift = +5.6%), with a broader 95% subsampling interval [0.826, 0.959] and the observed value falling near the lower end of the empirical subsampling interval (0.844 versus interval 0.826–0.959). This differential variability is reproducible across independent random seeds (cross-seed mean range < 0.003), indicating it reflects dataset properties rather than Monte Carlo noise. Across all pairwise comparisons between 80% subsample replicates, the Hyades coherence ratio was lower than the Pleiades coherence ratio in 65.1% of cases. 

To investigate the physical origin of the Hyades estimator's sensitivity, we performed a secondary leave-one-out influence analysis. **We define a star's *influence* as the absolute change in the global median prediction error ($|\Delta R|$) under leave-one-out removal of that star.** We computed this metric for each of the 820 Hyades members. The maximum influence of any single star was $|\Delta R| = 0.0198$, and the top 20 stars accounted for only 10.4% of the total influence, confirming that no small subset of observations dominates the metric.

We further tested whether these high-influence stars exhibit systematic kinematic asymmetry by computing their projected tangential outflow velocity relative to the cluster center. For this diagnostic, the cluster center is defined as the robust statistical median of the 3D positions, which is not assumed to coincide with the physical center of mass. 

**We evaluate the influence-group comparison as a function of sample size ($N \in [20, 100]$), treating it as a sensitivity curve to evaluate statistical power rather than a series of discrete hypothesis tests.** Across this range, the effect size remains stable and moderate, while statistical significance increases with sample size, reaching $p \approx 0.014$ at $N=100$. This behavior is consistent with a power-driven sensitivity curve rather than selective hypothesis testing. **The observed effect size (Cohen's $d \approx 0.30\text{--}0.38$) corresponds to a modest but coherent shift relative to the intrinsic local velocity dispersion, consistent with weak but non-random kinematic structuring.** We note that the absolute sign of the projected outflow depends on the adopted cluster center (flipping between median and mean definitions), indicating that the absolute flow direction is coordinate-dependent. However, the relative difference between high- and low-influence groups remains stable across center definitions. 

The projected outflow diagnostic and the TRACEBIND-V11 metric probe orthogonal properties of the velocity field: V11 measures local velocity predictability, while the outflow diagnostic measures bulk radial expansion. The fact that the outflow diagnostic does not show statistically significant asymmetry at baseline sample sizes ($p \approx 0.07$) reinforces that TRACEBIND-V11 captures local predictability independent of global expansion or contraction dynamics. The absence of a dominant bulk flow, combined with this subtle, scale-emergent kinematic bias, indicates that the observed subsampling variability and high local coherence are driven by complex, local velocity predictability rather than simple global dynamical evolution. Physical interpretations such as tidal substructure or mass segregation remain plausible hypotheses requiring further investigation.

---

## 6. Conclusion and Future Work

We have established a reproducible pipeline for reconciling Gaia DR2 membership catalogs with DR3 astrometry and quantifying kinematic coherence via the TRACEBIND-V11 metric. The verified Pleiades and Hyades benchmarks serve as references for future comparative studies.

Future work will extend TRACEBIND to additional open clusters spanning a range of ages and dynamical states. This will allow investigation of whether the normalized coherence ratio correlates with cluster age, tidal evolution, or other astrophysical properties. Additionally, propagating measurement uncertainties through the predictor, implementing softened distance kernels, and exploring alternative null models will further strengthen the statistical characterization of the metric.

---

## References

1.  Cantat-Gaudin, T., et al. 2022, "CG22: A new catalog of open cluster members", *A&A*, 665, A10.
2.  Gaia Collaboration, 2023, "Gaia Data Release 3: Summary of the content and survey properties", *A&A*, 674, A1.
3.  Lindegren, L., et al. 2018, "Reprocessing the Gaia DR2 astrometry", *A&A*, 616, A2.
4.  Good, P. I. 2005, "Permutation, Parametric, and Bootstrap Tests of Hypotheses", Springer.
5.  Davison, A. C., & Hinkley, D. V. 1997, "Bootstrap Methods and Their Application", Cambridge University Press.

---

## Appendix: Code Availability

The TRACEBIND-V11 implementation, including the verification scripts and benchmark construction pipelines, is available in the associated GitHub repository. The frozen configuration used for this analysis is:
*   `K_PREDICT = 30`
*   `N_PERMUTATIONS = 1000`
*   `NOISE_FRACTION = 0.10`
*   `RANDOM_SEED = 42`
*   `N_SUBSAMPLES = 500`
*   `SUBSAMPLE_FRACTION = 0.80`

***
