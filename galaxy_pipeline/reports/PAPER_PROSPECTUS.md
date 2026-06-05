\# Paper Prospectus: Methodology \& Validation



\*\*Proposed Title:\*\* 

\*A Directional Coherence Metric for Stellar Kinematic Fields: Statistical Properties and Out-of-Sample Validation\*



\*\*Target Journals:\*\* 

\*Publications of the Astronomical Society of the Pacific (PASP)\*, \*Astronomy \& Computing\*, or \*Research Notes of the AAS (RNAAS)\*.



\## Core Thesis

We introduce a robust, computationally efficient directional-coherence statistic ($C\_f$) for stellar proper-motion fields. We demonstrate that $C\_f$ is mathematically equivalent to the Mean Resultant Length ($R$) from circular statistics, and we rigorously evaluate its statistical properties, independence from spatial coordinates, and sensitivity to local kinematic alignment using Gaia DR3 data.



\## Established Claims (The "Yes" Pile)

1\. \*\*Mathematical Equivalence:\*\* $C\_f$ maps perfectly to standard circular statistics ($\\sigma \\approx \\sqrt{-2\\ln(C\_f)}$ with RMSE $\\approx 0$).

2\. \*\*Coordinate Independence:\*\* $C\_f$ is not a trivial proxy for Galactic latitude ($r = -0.177, p = 0.704$).

3\. \*\*Statistical Significance:\*\* Permutation testing confirms that high-$C\_f$ regions represent statistically unusual directional alignment, not random chance or global survey biases.

4\. \*\*Reproducibility:\*\* The metric is stable under bootstrap resampling and robust to the inclusion of unit-vector normalization.



\## Rejected/Deferred Claims (The "No" Pile)

1\. \*\*Stream Discovery:\*\* Monte Carlo cross-matching ($p = 1.0$) shows $C\_f$ does not preferentially overlap a crude catalog of known streams at current resolutions.

2\. \*\*Gravitational Physics:\*\* $C\_f$ provides no evidence regarding Dark Matter, MOND, or Emergent Gravity.

3\. \*\*Physical Compactness:\*\* Current 3D voxel tests show weak correlation between $C\_f$ and distance/speed dispersion.



\## Future Work (To be included in the paper's "Discussion" section)

\* \*\*3D Kinematics:\*\* Integrating Gaia DR3 Radial Velocities (RVS) to test if 2D directional coherence survives in full 3D phase-space.

\* \*\*Higher Resolution Mapping:\*\* Scaling from $13 \\times 7$ binning to HEALPix or $25 \\times 13$ grids to resolve narrower stellar streams.

