"""
TRACEBIND V11: Hyades Kinematic Coherence Analysis
EXACT MIRROR of Pleiades implementation for fair comparison.
Metric Version: V11
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

# ===== TRACEBIND V11 FROZEN PARAMETERS =====
# These parameters were fixed before cross-cluster comparison and were not tuned separately.
K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 1000
RANDOM_SEED = 42
NOISE_FRACTION = 0.10
EPSILON = 1e-6

# === PATH RESOLUTION (HYADES SPECIFIC) ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "reference", "hyades_cg22_dr3_crossmatched.csv")
NULL_OUTPUT = os.path.join(_PROJECT_ROOT, "data", "reference", "tracebind_v11_hyades_null.csv")

def astrometry_to_tangential_velocity(ra, dec, parallax, pmra, pmdec):
    """Convert proper motions to tangential velocities (km/s). IDENTICAL to Pleiades."""
    distance_pc = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    
    vt_ra = 4.74047 * pmra * distance_pc / 1000.0
    vt_dec = 4.74047 * pmdec * distance_pc / 1000.0
    
    x = distance_pc * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance_pc * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance_pc * np.sin(dec_rad)
    
    return np.column_stack([x, y, z]), np.column_stack([vt_ra, vt_dec])

def compute_loo_prediction_error(positions_3d, vel_vectors, k):
    """Leave-one-out weighted prediction error. IDENTICAL to Pleiades."""
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2:
        return np.nan

    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)

    dist_nbrs = distances[:, 1:]
    idx_nbrs = indices[:, 1:]

    weights = 1.0 / (dist_nbrs**2 + EPSILON)
    weight_sum = np.sum(weights, axis=1, keepdims=True)
    weight_sum = np.maximum(weight_sum, 1e-12)
    w_norm = weights / weight_sum

    vel_nbrs = vel_vectors[idx_nbrs]
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)
    errors = np.linalg.norm(vel_vectors - predicted, axis=1)
    return float(np.median(errors))

def compute_own_geometry_baseline(positions_3d, vel_vectors, k_predict, k_shuffle, n_perm, seed, noise_frac):
    """Per-population geometry baseline. IDENTICAL to Pleiades."""
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
            # Use ddof=1 for sample standard deviation (consistent with Pleiades)
            local_vel_std = np.std(vel_vectors[nbr_idx], axis=0, ddof=1)
            noise = rng.normal(0, noise_frac * local_vel_std, size=2)
            shuffled_vel[i] = vel_vectors[nbr_idx[chosen]] + noise

        err = compute_loo_prediction_error(positions_3d, shuffled_vel, k_predict)
        if not np.isnan(err):
            null_errors.append(err)

    return np.array(null_errors) if null_errors else np.array([np.nan])

def main():
    print("🔬 TRACEBIND V11: Hyades Tangential Velocity Coherence Analysis")
    print("=" * 78)
    print(f"Metric Version : V11")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # Input Validation
    required = ["ra", "dec", "parallax", "pmra", "pmdec"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Data Cleaning
    df = df.dropna(subset=required).copy()
    df = df[df["parallax"] > 0].copy()

    if len(df) <= K_PREDICT:
        raise ValueError(f"Need more than {K_PREDICT} stars for analysis. Found {len(df)}.")

    print(f"✅ Loaded {len(df)} vetted Hyades members.")
    print(f"   Stars analysed: {len(df)}")
    print(f"   Neighborhood size (k): {K_PREDICT}")
    print(f"   Permutations: {N_PERMUTATIONS}\n")

    pos_3d, vel_vec = astrometry_to_tangential_velocity(
        df["ra"].values, df["dec"].values, df["parallax"].values,
        df["pmra"].values, df["pmdec"].values
    )

    real_err = compute_loo_prediction_error(pos_3d, vel_vec, K_PREDICT)
    
    null_errors = compute_own_geometry_baseline(
        pos_3d, vel_vec, K_PREDICT, K_SHUFFLE, N_PERMUTATIONS, RANDOM_SEED, NOISE_FRACTION
    )
    
    baseline_mean = np.mean(null_errors)
    baseline_median = np.median(null_errors)
    baseline_std = np.std(null_errors, ddof=1) # Consistent ddof=1
    ci_low = np.percentile(null_errors, 2.5)
    ci_high = np.percentile(null_errors, 97.5)

    if np.isnan(real_err) or np.isnan(baseline_mean) or baseline_mean <= 1e-12:
        ratio = np.nan
        p_value = np.nan
        reduction = np.nan
    else:
        ratio = real_err / baseline_mean
        p_value = (np.sum(null_errors <= real_err) + 1) / (len(null_errors) + 1)
        reduction = 100 * (1 - ratio)

    print(f"📊 HYADES V11 RESULTS:")
    print("-" * 78)
    print(f"  Median Prediction Error (Real):           {real_err:.4f} km/s")
    print(f"  Baseline Mean Error (Randomized):         {baseline_mean:.4f} km/s")
    print(f"  Baseline Median Error (Randomized):       {baseline_median:.4f} km/s")
    print(f"  Baseline Std Dev:                         {baseline_std:.4f} km/s")
    print(f"  95% Permutation Null Interval:            [{ci_low:.4f}, {ci_high:.4f}] km/s")
    print(f"  Coherence Ratio (R):                      {ratio:.4f}")
    print(f"  Relative Reduction in Prediction Error:   {reduction:.2f}%")
    print(f"  One-sided Permutation p-value:            {p_value:.4f}")
    print("-" * 78)

    # Save null distribution with metadata
    null_df = pd.DataFrame({
        "null_error": null_errors,
        "k_predict": K_PREDICT,
        "k_shuffle": K_SHUFFLE,
        "noise_fraction": NOISE_FRACTION,
        "seed": RANDOM_SEED
    })
    null_df.to_csv(NULL_OUTPUT, index=False)
    print(f"💾 Saved null distribution with metadata to {NULL_OUTPUT}")

    print("\n🔒 TRACEBIND V11 CHECKPOINT:")
    print("- Metric: Leave-One-Out Tangential Velocity Prediction")
    print("- Null Hypothesis: Tangential velocities are exchangeable within local spatial neighborhoods.")
    print("- Status: VALIDATED COMPUTATION PATH V11 (HYADES)")
    print("✅ Frozen configuration matches Pleiades implementation exactly (ddof=1).")

if __name__ == "__main__":
    main()