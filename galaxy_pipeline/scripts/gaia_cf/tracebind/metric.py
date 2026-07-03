"""
TRACEBIND Locked V11 Metric — Single Source of Truth
License: CC0 1.0 Universal
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors

TRACEBIND_METRIC_VERSION = "V11"

def astrometry_to_cartesian(ra, dec, parallax):
    """Inverse-parallax distance conversion.
    DOCUMENTED LIMITATION: Not full covariance propagation."""
    parallax = np.clip(parallax, 1e-6, None)
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])

def compute_loo_prediction_error(positions_3d, pmra, pmdec, k):
    """Locked V11 LOO predictor."""
    n = len(positions_3d)
    safe_k = min(k + 1, n)
    if safe_k < 2: return np.nan
    pm_vectors = np.column_stack([pmra, pmdec])
    nn = NearestNeighbors(n_neighbors=safe_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)
    dist_nbrs = distances[:, 1:]
    idx_nbrs = indices[:, 1:]
    eps = 1e-6
    weights = 1.0 / (dist_nbrs**2 + eps)
    w_norm = weights / np.sum(weights, axis=1, keepdims=True)
    vel_nbrs = pm_vectors[idx_nbrs]
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)
    errors = np.linalg.norm(pm_vectors - predicted, axis=1)
    return float(np.median(errors))

def compute_ratio_distribution(positions_3d, pmra, pmdec, k_predict, k_shuffle, n_perm, rng):
    """Compute ratio distribution: real_error / null_errors."""
    real_err = compute_loo_prediction_error(positions_3d, pmra, pmdec, k_predict)
    if np.isnan(real_err): return np.array([])
    pm_vectors = np.column_stack([pmra, pmdec])
    n = len(positions_3d)
    safe_k_shuf = min(max(k_predict + 1, k_shuffle), n)
    nn = NearestNeighbors(n_neighbors=safe_k_shuf, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    _, indices_all = nn.kneighbors(positions_3d)
    null_errors = []
    for _ in range(n_perm):
        shuffled_pm = np.empty_like(pm_vectors)
        for i in range(n):
            nbr_idx = indices_all[i, 1:safe_k_shuf]
            if len(nbr_idx) == 0: shuffled_pm[i] = pm_vectors[i]; continue
            chosen = rng.integers(0, len(nbr_idx))
            local_vel_std = np.std(pm_vectors[nbr_idx], axis=0)
            noise = rng.normal(0, 0.1 * local_vel_std, size=2)
            shuffled_pm[i] = pm_vectors[nbr_idx[chosen]] + noise
        err = compute_loo_prediction_error(positions_3d, shuffled_pm[:, 0], shuffled_pm[:, 1], k_predict)
        if not np.isnan(err): null_errors.append(err)
    if len(null_errors) < 10: return np.array([])
    return real_err / np.array(null_errors)