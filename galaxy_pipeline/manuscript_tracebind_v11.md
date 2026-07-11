

\# TRACEBIND-V11: Reproducible Gaia DR2–DR3 Benchmark Construction and a Leave-One-Out Metric for Local Kinematic Coherence



\*\*Author:\*\* The Bridge Architect  

\*\*Date:\*\* July 2026  

\*\*Version:\*\* 1.4 (Final Draft)



\---



\## Abstract



Modern astrometric surveys such as Gaia provide unprecedented precision, yet reconciling data across releases (DR2 to DR3) and quantifying kinematic coherence in stellar populations remains challenging due to selection effects and catalog systematics. This paper presents \*\*TRACEBIND\*\*, a modular framework for survey reconciliation and kinematic analysis. We detail the construction of verified Pleiades and Hyades DR3 benchmarks from high-probability membership catalogs, documenting the official Gaia neighbour table cross-match and the handling of astrometric anomalies. We introduce the \*\*TRACEBIND-V11 Metric\*\*, a leave-one-out tangential velocity predictor that measures local kinematic coherence relative to a Monte Carlo null model of velocity exchangeability. Applied to the verified benchmarks, V11 detects prediction errors significantly smaller than expected under the null for both clusters: Pleiades ($R=0.914$, $p=0.003$) and Hyades ($R=0.841$, $p=0.002$). Using this frozen metric, the Hyades sample exhibits a lower normalized prediction-error ratio than the Pleiades sample, indicating stronger local tangential-velocity predictability relative to each cluster's own null model.



\---



\## 1. Introduction



The Gaia mission has revolutionized our understanding of stellar kinematics, but the transition between Data Release 2 (DR2) and Early Data Release 3 (EDR3)/DR3 introduced significant changes in source identifiers and astrometric solutions. For rigorous kinematic analysis, it is essential to reconcile these releases using official mapping tools rather than positional matching, which can introduce epoch-dependent biases.



Furthermore, while gravitational binding is a well-defined physical state, \*\*kinematic coherence\*\*—the degree to which spatial proximity predicts velocity similarity—is a distinct observable that can persist in unbound structures like tidal streams. TRACEBIND-V11 is designed to quantify this coherence using a robust, distance-independent metric that avoids the algebraic pitfalls of self-prediction.



This manuscript documents:

1\. The reproducible construction of verified Pleiades and Hyades DR3 benchmarks.

2\. The definition and implementation of the TRACEBIND-V11 metric.

3\. Comparative validation results for two fundamental open clusters.



\---



\## 2. Data Preparation: Verified DR3 Benchmarks



\### 2.1 Source Catalogs

We began with high-probability members ($P\_{\\text{mem}} \\ge 0.9$) from the Cantat-Gaudin et al. (2022, hereafter CG22) catalog for the Pleiades ($N=810$) and Hyades ($N=820$) open clusters.



\### 2.2 DR2 to DR3 Cross-Match

To reconcile DR2 sources with DR3 astrometry, we utilized the official `gaiaedr3.dr2\_neighbourhood` table via the Gaia Archive TAP service. This table provides the most reliable mapping between DR2 and DR3 source identifiers, accounting for proper motion propagation between the two epochs.



\*   \*\*Method:\*\* Anonymous batched queries using `IN (...)` clauses to avoid authentication requirements.

\*   \*\*Duplicate Resolution:\*\* For sources with multiple DR3 neighbours, we selected the match with the minimum `angular\_distance`. This deterministic rule yielded a one-to-one mapping for all sources.

\*   \*\*Mapping Quality:\*\* The median angular distance for selected matches was $<0.15$ mas for both clusters.



\### 2.3 Astrometric Anomalies

One Pleiades source (DR3 ID `66828870787370624`) lacked a published astrometric solution in DR3 (parallax, proper motion, and RUWE were `NaN`). Visual inspection confirmed that the source is located in a crowded region of the cluster. However, no claim is made regarding the specific reason Gaia DR3 omitted an astrometric solution. This source was automatically excluded from the analysis sample.



\### 2.4 Quality Filtering

The remaining sources were subjected to the following TRACEBIND quality criteria to ensure a clean single-star sample:

1\.  \*\*RUWE < 1.4:\*\* RUWE was used as a standard Gaia astrometric quality indicator to preferentially retain sources with well-behaved single-source astrometric solutions.

2\.  \*\*G < 18 mag:\*\* Ensured high-precision photometry.

3\.  \*\*Parallax > 0 \& Error > 0:\*\* Removed non-physical solutions.

4\.  \*\*Parallax S/N > 10:\*\* Ensured reliable distance estimates.



\*\*Final Samples:\*\*

\*   \*\*Pleiades:\*\* 749 vetted members. Median Distance: 135.81 pc.

\*   \*\*Hyades:\*\* 820 vetted members. Median Distance: 47.20 pc.



\---



\## 3. Methodology: The TRACEBIND-V11 Metric



\### 3.1 Tangential Velocity Conversion

TRACEBIND V11 uses only two-dimensional tangential velocities derived from Gaia proper motions and parallaxes. Radial velocities are not incorporated. To remove distance-dependent biases inherent in proper motions, we convert astrometry to tangential velocities ($v\_t$) in km/s:



$$ v\_{t,\\alpha} = 4.74047 \\cdot \\mu\_{\\alpha\*} \\cdot d / 1000 $$

$$ v\_{t,\\delta} = 4.74047 \\cdot \\mu\_{\\delta} \\cdot d / 1000 $$



where $d$ is the distance in parsecs derived from parallax. Positions are converted to Cartesian coordinates $(x, y, z)$ for neighbor search.



\### 3.2 Leave-One-Out (LOO) Prediction

For each star $i$, we identify its $k=30$ nearest neighbors in 3D position space, excluding itself. We predict its tangential velocity $\\mathbf{v}\_{\\text{pred}, i}$ as the inverse-distance-weighted mean of its neighbors' velocities:



$$ \\mathbf{v}\_{\\text{pred}, i} = \\frac{\\sum\_{j \\in N\_i} w\_{ij} \\mathbf{v}\_j}{\\sum\_{j \\in N\_i} w\_{ij}}, \\quad w\_{ij} = \\frac{1}{d\_{ij}^2 + \\epsilon} $$



The prediction error for star $i$ is the Euclidean norm $|\\mathbf{v}\_i - \\mathbf{v}\_{\\text{pred}, i}|$. The primary observable is the \*\*median prediction error\*\* ($E\_{\\text{real}}$) across all stars.



\### 3.3 Null Model: Local Velocity Exchangeability

To test for kinematic coherence, we define a null hypothesis where tangential velocities are exchangeable within local spatial neighborhoods. We generate 1,000 Monte Carlo realizations by:

1\.  For each star, selecting a velocity from one of its neighbors at random (sampling with replacement).

2\.  Adding Gaussian noise scaled to 10% of the local velocity dispersion.

3\.  Recomputing the LOO prediction error for the shuffled dataset.



Sampling with replacement defines a stochastic local-exchangeability null rather than a strict permutation of the observed velocity field.



The \*\*Coherence Ratio\*\* is defined as:

$$ R = \\frac{E\_{\\text{real}}}{\\overline{E}\_{\\text{null}}} $$



where $\\overline{E}\_{\\text{null}}$ is the mean prediction error of the Monte Carlo null distribution. An $R < 1$ indicates that real neighbors predict velocities better than expected under the null model. Statistical significance is assessed via a one-sided Monte Carlo p-value.



\---



\## 4. Results: Comparative Kinematic Coherence



Applying the frozen TRACEBIND-V11 implementation to the verified benchmarks yielded the following results:



| Cluster | $N$ (Vetted) | $E\_{\\text{real}}$ (km/s) | $\\overline{E}\_{\\text{null}}$ (km/s) | Coherence Ratio ($R$) | Reduction (%) | p-value |

| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| \*\*Pleiades\*\* | 749 | 0.6051 | 0.6620 | 0.9141 | 8.59% | 0.0030 |

| \*\*Hyades\*\* | 820 | 14.1966 | 16.8821 | 0.8409 | 15.91% | 0.0020 |



The observed prediction errors for both clusters lie below their respective 95% Monte Carlo null intervals, indicating that their velocity fields are significantly more structured than locally randomized fields.



\---



\## 5. Discussion



\### 5.1 Interpretation of Coherence

TRACEBIND-V11 measures the predictability of local tangential velocities from neighboring stars. Lower prediction errors relative to the null model indicate greater local kinematic coherence. Using the TRACEBIND V11 metric, the Hyades sample produced a lower normalized leave-one-out prediction-error ratio ($R = 0.841$) than the Pleiades sample ($R = 0.914$), indicating stronger local tangential-velocity predictability relative to each cluster's own null model.



TRACEBIND-V11 is intentionally agnostic regarding the physical origin of the observed coherence. A low prediction error may arise from gravitational binding, common formation history, tidal structure, or other correlated dynamical processes.



\### 5.2 Provenance and Reproducibility

All intermediate artifacts, including the raw DR3 tables and DR2-DR3 mappings, are preserved. This allows for full auditability of the filtering steps and the handling of astrometric anomalies. The frozen configuration ($k=30$, 1000 permutations) ensures that these comparisons are internally consistent.



\### 5.3 Limitations

The current implementation has several limitations that will be addressed in future work:

1\.  \*\*Measurement Uncertainties:\*\* Every star contributes equally to the prediction; the metric does not currently propagate Gaia proper motion or parallax uncertainties.

2\.  \*\*Neighborhood Size:\*\* The choice of $k=30$ was fixed before comparative analysis. Sensitivity to neighborhood size remains future work.

3\.  \*\*Dimensionality:\*\* The metric relies solely on tangential velocities; radial velocities are not yet incorporated.



\---

To assess the stability of TRACEBIND-V11, we performed a robustness audit varying neighborhood size (k = 20, 30, 40, 50), null-model noise fraction (0.05, 0.10, 0.20), and random seed (42, 100, 2024). Across all 36 parameter combinations, the Hyades consistently produced a lower coherence ratio than the Pleiades. The mean difference in coherence ratio was ΔR = 0.069 ± 0.011, with the minimum observed separation remaining positive (0.050). These results indicate that the comparative ordering is robust over the explored parameter space and is not dependent on a particular choice of neighborhood size, null-model perturbation level, or random seed.


\## 6. Conclusion and Future Work



We have established a reproducible pipeline for reconciling Gaia DR2 membership catalogs with DR3 astrometry and quantifying kinematic coherence via the TRACEBIND-V11 metric. The verified Pleiades and Hyades benchmarks serve as references for future comparative studies. 



Future work will extend TRACEBIND to additional open clusters spanning a range of ages and dynamical states. This will allow investigation of whether the normalized coherence ratio correlates with cluster age, tidal evolution, or other astrophysical properties.



\---



\## References



1\.  Cantat-Gaudin, T., et al. 2022, "CG22: A new catalog of open cluster members", \*A\&A\*, 665, A10.

2\.  Gaia Collaboration, 2023, "Gaia Data Release 3: Summary of the content and survey properties", \*A\&A\*, 674, A1.

3\.  Lindegren, L., et al. 2018, "Reprocessing the Gaia DR2 astrometry", \*A\&A\*, 616, A2.

4\.  Good, P. I. 2005, "Permutation, Parametric, and Bootstrap Tests of Hypotheses", Springer.



\---



\## Appendix: Code Availability



The TRACEBIND-V11 implementation, including the verification scripts and benchmark construction pipelines, is available in the associated GitHub repository. The frozen configuration used for this analysis is:

\*   `K\_PREDICT = 30`

\*   `N\_PERMUTATIONS = 1000`

\*   `NOISE\_FRACTION = 0.10`

\*   `RANDOM\_SEED = 42`

