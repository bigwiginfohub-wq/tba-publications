"""
TRACEBIND V11 Core Logic
Single source of truth for all V11 computations.
Refactored to use structured neighbor graph dictionaries.
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors

EPSILON = 1e-6


def astrometry_to_tangential_velocity(ra, dec, parallax, pmra, pmdec):
    """Convert proper motions to tangential velocities (km/s)."""
    distance_pc = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)

    vt_ra = 4.74047 * pmra * distance_pc / 1000.0
    vt_dec = 4.74047 * pmdec * distance_pc / 1000.0

    x = distance_pc * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance_pc * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance_pc * np.sin(dec_rad)

    return np.column_stack([x, y, z]), np.column_stack([vt_ra, vt_dec])


def build_neighbor_graph(positions_3d, max_k):
    """
    Build the full neighbor graph once at max_k.
    Returns a dictionary containing distances and indices (excluding self).
    """
    n = len(positions_3d)
    safe_max_k = min(max_k + 1, n)

    nn = NearestNeighbors(n_neighbors=safe_max_k, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    distances, indices = nn.kneighbors(positions_3d)

    # Exclude self (index 0) from both arrays
    return {
        "distances": distances[:, 1:],
        "indices": indices[:, 1:]
    }


def _get_weights_and_indices(graph, k):
    """Slice the precomputed graph to the requested k and compute weights."""
    idx_nbrs = graph["indices"][:, :k]
    dist_nbrs = graph["distances"][:, :k]

    weights = 1.0 / (dist_nbrs**2 + EPSILON)
    weight_sum = np.sum(weights, axis=1, keepdims=True)
    w_norm = weights / np.maximum(weight_sum, 1e-12)

    return w_norm, idx_nbrs


def compute_loo_prediction_error(vel_vectors, k, graph):
    """Leave-one-out weighted prediction error using precomputed graph."""
    if graph["indices"].shape[1] < k:
        raise ValueError(f"Graph has only {graph['indices'].shape[1]} neighbors but k={k} was requested.")

    w_norm, idx_nbrs = _get_weights_and_indices(graph, k)

    vel_nbrs = vel_vectors[idx_nbrs]
    predicted = np.sum(w_norm[:, :, np.newaxis] * vel_nbrs, axis=1)
    errors = np.linalg.norm(vel_vectors - predicted, axis=1)
    return float(np.median(errors))


def compute_own_geometry_baseline(vel_vectors, k_predict, k_shuffle, n_perm, seed, noise_frac, graph):
    """Per-population geometry baseline with SELF-EXCLUSION."""
    rng = np.random.default_rng(seed)
    n = len(vel_vectors)

    # Slice graph for shuffle neighborhood
    _, idx_shuffle = _get_weights_and_indices(graph, k_shuffle)

    null_errors = []
    for _ in range(n_perm):
        shuffled_vel = np.empty_like(vel_vectors)
        for i in range(n):
            nbr_idx = idx_shuffle[i]
            if len(nbr_idx) == 0:
                shuffled_vel[i] = vel_vectors[i]
                continue

            chosen = rng.integers(0, len(nbr_idx))
            local_vel_std = np.std(vel_vectors[nbr_idx], axis=0, ddof=1)
            noise = rng.normal(0, noise_frac * local_vel_std, size=2)
            shuffled_vel[i] = vel_vectors[nbr_idx[chosen]] + noise

        # CRITICAL: Use the SAME function as the real error calculation
        err = compute_loo_prediction_error(shuffled_vel, k_predict, graph)
        if not np.isnan(err):
            null_errors.append(err)

    return np.array(null_errors) if null_errors else np.array([np.nan])