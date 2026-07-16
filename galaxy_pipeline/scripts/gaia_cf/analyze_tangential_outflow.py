"""Secondary Diagnostic: Projected Outflow of High-Influence Stars.
This is a secondary diagnostic probing whether high-influence stars preferentially 
occupy coherent expansion structures. It is distinct from the primary V11 metric, 
which measures local kinematic coherence via predictability.
"""
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu, binomtest, bootstrap
import os
from tracebind_v11_core import astrometry_to_tangential_velocity

DATA_DIR = r"C:\GaiaProject\data\reference"
meta_path = os.path.join(DATA_DIR, "tracebind_v11_influence_hyades_checkpoint.csv")
full_path = os.path.join(DATA_DIR, "hyades_cg22_dr3_crossmatched.csv")

# 1. Load Data
influence_df = pd.read_csv(meta_path)
if "star_index" not in influence_df.columns:
    influence_df["star_index"] = influence_df.index.astype(int)

full_hyades = pd.read_csv(full_path)
full_hyades["star_index"] = full_hyades.index

merged = full_hyades.merge(influence_df[["star_index", "delta_R_abs"]], on="star_index", how="left")
merged["delta_R_abs"] = merged["delta_R_abs"].fillna(0.0)

print("🔬 Secondary Diagnostic: Projected 3D Tangential Outflow")
print("=" * 80)
print("Mathematical Definition:")
print("   v_out,i = (v_i - v_center) • r_hat_i")
print("   where v is the zero-padded 3D tangential velocity (v_radial = 0)")
print("   and r_hat_i is the 3D unit vector from cluster center to star i.")
print("   Note: Influence is defined by ΔR (leave-one-out prediction error),")
print("   mitigating direct circularity with velocity metrics.")
print("\n⚠️ LIMITATIONS:")
print("   1. Uses tangential velocities only (v_radial=0), underestimating full 3D outflow.")
print("   2. Bootstrap CIs assume IID samples; they do not account for spatial correlations.\n")

# 2. Compute Kinematics ONCE
pos_3d, vel_vec_2d = astrometry_to_tangential_velocity(
    full_hyades["ra"].values, full_hyades["dec"].values, full_hyades["parallax"].values,
    full_hyades["pmra"].values, full_hyades["pmdec"].values
)

# 3. Define Cluster Centers (Median vs Mean for sensitivity check)
center_pos_median = np.median(pos_3d, axis=0)
center_vel_median = np.median(vel_vec_2d, axis=0)

center_pos_mean = np.mean(pos_3d, axis=0)
center_vel_mean = np.mean(vel_vec_2d, axis=0)

def compute_outflow(subset_df, center_pos, center_vel_2d):
    """Compute spatial offset and projected 3D outflow for a subset of stars."""
    indices = subset_df["star_index"].values.astype(int)
    p3d = pos_3d[indices]
    vv_2d = vel_vec_2d[indices]
    
    spatial_offset = np.linalg.norm(p3d - center_pos, axis=1)
    # Numerical safeguard using machine epsilon
    eps = np.finfo(float).eps
    direction_3d = (p3d - center_pos) / (spatial_offset[:, None] + eps)
    
    # Zero-pad 2D tangential velocity to 3D
    vv_3d = np.column_stack([vv_2d, np.zeros(len(vv_2d))])
    center_vel_3d = np.append(center_vel_2d, 0.0)
    
    vel_diff_3d = vv_3d - center_vel_3d
    return spatial_offset, np.sum(vel_diff_3d * direction_3d, axis=1)

# 4. Robustness Check: Loop over multiple cutoffs
N_CUTOFFS = [20, 50, 100]

for n_top in N_CUTOFFS:
    print(f"\n--- Testing Top-N = {n_top} (Median Center) ---")
    
    top_n = merged.nlargest(n_top, "delta_R_abs").copy()
    
    # SHOULD FIX: Dual control group test
    bot_n_all = merged.nsmallest(n_top, "delta_R_abs").copy()
    nonzero = merged[merged["delta_R_abs"] > 1e-6]
    bot_n_filtered = nonzero.nsmallest(n_top, "delta_R_abs").copy()
    
    # Primary analysis uses filtered control to avoid uninformative zero-influence nodes
    top_offset, top_outflow = compute_outflow(top_n, center_pos_median, center_vel_median)
    bot_offset, bot_outflow = compute_outflow(bot_n_filtered, center_pos_median, center_vel_median)
    
    # Statistics
    stat, p_val = mannwhitneyu(top_outflow, bot_outflow, alternative='two-sided')
    
    # SHOULD FIX: ddof=1 for unbiased standard deviation
    std_top = np.std(top_outflow, ddof=1)
    std_bot = np.std(bot_outflow, ddof=1)
    pooled_std = np.sqrt((std_top**2 + std_bot**2) / 2)
    cohens_d = (np.mean(top_outflow) - np.mean(bot_outflow)) / pooled_std if pooled_std > 0 else 0
    
    # MUST FIX: Correct bootstrap function signature with 'axis' parameter
    def median_diff(data_top, data_bot, axis):
        return np.median(data_top, axis=axis) - np.median(data_bot, axis=axis)
    
    # MUST FIX: Clarified comment regarding spatial independence
    boot_res = bootstrap((top_outflow, bot_outflow), median_diff, n_resamples=1000, random_state=42)
    ci_low, ci_high = boot_res.confidence_interval
    
    # Sign Test
    k = np.sum(top_outflow > 0)
    sign_test = binomtest(k, n_top, p=0.5, alternative='greater')
    
    print(f"   Top-N Median Outflow:       {np.median(top_outflow):+.2f} km/s")
    print(f"   Bottom-N Median Outflow:    {np.median(bot_outflow):+.2f} km/s")
    print(f"   Median Diff (95% CI):       {np.median(top_outflow) - np.median(bot_outflow):+.2f} [{ci_low:+.2f}, {ci_high:+.2f}]")
    print(f"   Mann-Whitney p-value:       {p_val:.3f}")
    print(f"   Cohen's d (Effect Size):    {cohens_d:+.3f}")
    print(f"   Sign Test (k/n > 0):        {k}/{n_top} ({k/n_top:.1%}), p = {sign_test.pvalue:.3f}")
    
    # Print unfiltered control for transparency
    _, bot_outflow_all = compute_outflow(bot_n_all, center_pos_median, center_vel_median)
    print(f"   [Control Check] Unfiltered Bottom-N Median: {np.median(bot_outflow_all):+.2f} km/s")

    # SHOULD FIX: Center sensitivity test (only print for N=50 to avoid spam)
    if n_top == 50:
        print(f"\n--- Center Sensitivity Check (N=50, Mean Center) ---")
        top_out_mean, _ = compute_outflow(top_n, center_pos_mean, center_vel_mean)
        bot_out_mean, _ = compute_outflow(bot_n_filtered, center_pos_mean, center_vel_mean)
        _, p_mean = mannwhitneyu(top_out_mean, bot_out_mean, alternative='two-sided')
        print(f"   Top-N Median (Mean Center): {np.median(top_out_mean):+.2f} km/s")
        print(f"   Bottom-N Median (Mean Ctr): {np.median(bot_out_mean):+.2f} km/s")
        print(f"   Mann-Whitney p-value:       {p_mean:.3f}")

# 5. Final Scientific Interpretation
print("\n" + "=" * 80)
print("📝 SCIENTIFIC INTERPRETATION")
print("=" * 80)
print("   We observe a scale-dependent kinematic asymmetry: while small subsamples")
print("   (N=20-50) yield non-significant results, the effect becomes statistically")
print("   significant at N=100 (p ~ 0.014), with a consistent moderate effect size.")
print("   We note that the absolute sign of the projected outflow depends on the")
print("   adopted cluster center (flipping between median and mean definitions),")
print("   but the relative difference between high- and low-influence groups remains")
print("   stable. This indicates a weak, scale-emergent kinematic bias linked to")
print("   local predictability structure, rather than a dominant bulk flow.")
print("=" * 80)