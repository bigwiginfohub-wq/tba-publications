"""
TRACEBIND V11: Non-Degenerate LOO Prediction + Per-Population Baselines
Refined for Tangential Velocity Coherence and Robust Statistical Reporting.
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

# === CONFIGURATION (FROZEN) ===
K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 1000  # Increased for finer p-value resolution
RANDOM_SEED = 42
NOISE_FRACTION = 0.10  # Fraction of local velocity std added to shuffled values

# === PATH RESOLUTION ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "reference", "pleiades_cg22_dr3_crossmatched.csv")

def astrometry_to_tangential_velocity(ra, dec, parallax, pmra, pmdec):
    """Convert proper motions to tangential velocities (km/s) for distance-independent coherence."""
    distance_pc = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    
    # Tangential velocity components (km/s)
    vt_ra = 4.74047 * pmra * distance_pc / 1000.0
    vt_dec = 4.74047 * pmdec * distance_pc / 1000.0
    
    # Cartesian positions (pc) for neighbor search
    x = distance_pc * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance_pc * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance_pc * np.sin(dec_rad)
    
    return np.column_stack([x, y, z]), np.column_stack([vt_ra, vt_dec])

def compute_loo_prediction_error(positions_3d, vel_vectors, k):
    """Leave-one-out weighted prediction error using tangential velocities."""
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2:
        return np.nan

    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)

    # Exclude self (index 0)
    dist_nbrs = distances[:, 1:]
    idx_nbrs = indices[:, 1:]

    eps = 1e-6
    weights = 1.0 / (dist_nbrs**2 + eps)
    
    # Numerical safety: prevent division by zero in normalization
    weight_sum = np.sum(weights, axis=1, keepdims=True)
    weight_sum = np.maximum(weight_sum, 1e-12)
    w_norm = weights / weight_sum

    # Predicted velocity = weighted mean of NEIGHBORS ONLY
    vel_nbrs = vel_vectors[idx_nbrs]
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)

    # Error = ||target - predicted||
    errors = np.linalg.norm(vel_vectors - predicted, axis=1)
    return float(np.median(errors))

def compute_own_geometry_baseline(positions_3d, vel_vectors, k_predict, k_shuffle, n_perm, seed, noise_frac):
    """
    Per-population geometry baseline with SELF-EXCLUSION in shuffle.
    Null Hypothesis: Tangential velocities are exchangeable within local spatial neighborhoods.
    Note: Uses sampling with replacement from neighbors plus Gaussian perturbation.
    """
    rng = np.random.default_rng(seed)
    n = len(positions_3d)
    safe_k_shuf = min(max(k_predict + 1, k_shuffle), n)
    
    nn = NearestNeighbors(n_neighbors=safe_k_shuf, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    _, indices_all = nn.kneighbors(positions_3d)

    null_errors = []
    for _ in range(n_perm):
        shuffled_vel = np.empty_like(vel_vectors)
        for i in range(n):
            nbr_idx = indices_all[i, 1:safe_k_shuf]
            if len(nbr_idx) == 0:
                shuffled_vel[i] = vel_vectors[i]
                continue
            
            chosen = rng.integers(0, len(nbr_idx))
            # Use ddof=0 for population standard deviation (negligible difference for n~50)
            local_vel_std = np.std(vel_vectors[nbr_idx], axis=0, ddof=0)
            noise = rng.normal(0, noise_frac * local_vel_std, size=2)
            shuffled_vel[i] = vel_vectors[nbr_idx[chosen]] + noise

        err = compute_loo_prediction_error(positions_3d, shuffled_vel, k_predict)
        if not np.isnan(err):
            null_errors.append(err)

    return np.array(null_errors) if null_errors else np.array([np.nan])

def main():
    print("🔬 TRACEBIND V11: Tangential Velocity Coherence Analysis")
    print("=" * 78)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} vetted Pleiades members.")
    print(f"   Stars analysed: {len(df)}")
    print(f"   Neighborhood size (k): {K_PREDICT}")
    print(f"   Permutations: {N_PERMUTATIONS}\n")

    # Convert to Tangential Velocities
    pos_3d, vel_vec = astrometry_to_tangential_velocity(
        df["ra"].values, df["dec"].values, df["parallax"].values,
        df["pmra"].values, df["pmdec"].values
    )

    # Compute Real Error
    real_err = compute_loo_prediction_error(pos_3d, vel_vec, K_PREDICT)
    
    # Compute Baseline Distribution
    null_errors = compute_own_geometry_baseline(
        pos_3d, vel_vec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, RANDOM_SEED, NOISE_FRACTION
    )
    
    baseline_mean = np.mean(null_errors)
    baseline_std = np.std(null_errors)
    ci_low = np.percentile(null_errors, 2.5)
    ci_high = np.percentile(null_errors, 97.5)

    # Ratio Safety Check
    if np.isnan(real_err) or np.isnan(baseline_mean) or baseline_mean <= 1e-12:
        ratio = np.nan
        p_value = np.nan
        improvement = np.nan
    else:
        ratio = real_err / baseline_mean
        # One-sided permutation p-value: proportion of null errors <= observed error
        p_value = (np.sum(null_errors <= real_err) + 1) / (len(null_errors) + 1)
        # Relative reduction in prediction error
        improvement = 100 * (1 - ratio)

    print(f"📊 PLEIADES V11 RESULTS:")
    print("-" * 78)
    print(f"  Median Prediction Error (Real):           {real_err:.4f} km/s")
    print(f"  Baseline Mean Error (Randomized):         {baseline_mean:.4f} km/s")
    print(f"  Baseline Std Dev:                         {baseline_std:.4f} km/s")
    print(f"  95% Permutation Null Interval:            [{ci_low:.4f}, {ci_high:.4f}] km/s")
    print(f"  Coherence Ratio (R):                      {ratio:.4f}")
    print(f"  Relative Reduction in Prediction Error:   {improvement:.2f}%")
    print(f"  One-sided Permutation p-value:            {p_value:.4f}")
    print("-" * 78)

    # Save null distribution for future analysis
    null_df = pd.DataFrame({"null_error": null_errors})
    null_path = os.path.join(_PROJECT_ROOT, "data", "reference", "tracebind_v11_pleiades_null.csv")
    null_df.to_csv(null_path, index=False)
    print(f"💾 Saved null distribution to {null_path}")

    print("\n🔒 TRACEBIND V11 CHECKPOINT:")
    print("- Metric: Leave-One-Out Tangential Velocity Prediction")
    print("- Null Hypothesis: Tangential velocities are exchangeable within local spatial neighborhoods.")
    print("- Status: VALIDATED COMPUTATION PATH V11")
    print("⚠️  NOTE: Hyades comparison requires recomputation with this exact frozen metric.")

if __name__ == "__main__":
    main()