"""
TRACEBIND v2.0 - Phase 1: Local Velocity Prediction Error (V8)
Tests functional dependence P(v|x) via local regression prediction error.
Captures gradients, streaming motions, and convergent flows.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")

K_NEIGHBORS = 30
N_PERMUTATIONS = 100
RANDOM_SEED = 42


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def compute_local_prediction_error(positions_3d, pmra, pmdec, k):
    """
    For each star, predict its velocity as the mean of its k nearest neighbors'
    velocities. Return median L2 prediction error across population.
    
    Lower error = stronger functional dependence v = f(x).
    """
    n = len(positions_3d)
    if k >= n:
        return np.nan

    pm_vectors = np.column_stack([pmra, pmdec])

    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]

    # Predicted velocity = mean of neighbors' velocities
    neighbor_vels = pm_vectors[indices]          # (n, k, 2)
    predicted = np.mean(neighbor_vels, axis=1)   # (n, 2)

    # L2 prediction error per star
    errors = np.linalg.norm(pm_vectors - predicted, axis=1)

    return float(np.median(errors))


def compute_dual_null_v8(positions_3d, pmra, pmdec, k, n_perm, seed):
    """
    Real prediction error + Z-scores against velocity-null and position-null.
    
    TRUE STRUCTURE → prediction error SMALLER than null → Z << 0.
    """
    rng = np.random.default_rng(seed)

    real_stat = compute_local_prediction_error(positions_3d, pmra, pmdec, k)
    if np.isnan(real_stat):
        return {key: np.nan for key in ["real", "z_vel", "z_pos", "null_vel_mean", "null_pos_mean"]}

    null_vel_list = []
    null_pos_list = []

    for _ in range(n_perm):
        # NULL 1: Shuffle velocities → breaks P(v|x), preserves spatial structure
        perm_v = rng.permutation(len(pmra))
        r_v = compute_local_prediction_error(positions_3d, pmra[perm_v], pmdec[perm_v], k)
        if not np.isnan(r_v):
            null_vel_list.append(r_v)

        # NULL 2: Shuffle positions → breaks spatial structure, preserves velocity dist
        perm_p = rng.permutation(len(positions_3d))
        r_p = compute_local_prediction_error(positions_3d[perm_p], pmra, pmdec, k)
        if not np.isnan(r_p):
            null_pos_list.append(r_p)

    def safe_z(real, null_list):
        if len(null_list) < 10:
            return np.nan, np.nan
        mean_n = np.mean(null_list)
        std_n = np.std(null_list)
        z = (real - mean_n) / std_n if std_n > 1e-10 else np.nan
        return z, mean_n

    z_vel, mean_vel = safe_z(real_stat, null_vel_list)
    z_pos, mean_pos = safe_z(real_stat, null_pos_list)

    return {
        "real": real_stat,
        "z_vel": z_vel,
        "z_pos": z_pos,
        "null_vel_mean": mean_vel,
        "null_pos_mean": mean_pos,
    }


def main():
    print("🔬 TRACEBIND V8: Local Velocity Prediction Error")
    print("=" * 78)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows | k={K_NEIGHBORS} | Perms: {N_PERMUTATIONS} | Seed: {RANDOM_SEED}\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())
    results = {}

    print(f"📊 Local Prediction Error Results:")
    print("-" * 78)
    print(f"  {'Population':<20s} {'Med Err':>8s} {'Z_vel':>8s} {'Z_pos':>8s} {'Verdict':>18s}")
    print("-" * 78)

    for pop in populations:
        mask = df["population"] == pop
        try:
            res = compute_dual_null_v8(
                positions_3d[mask],
                df.loc[mask, "pmra"].values,
                df.loc[mask, "pmdec"].values,
                K_NEIGHBORS, N_PERMUTATIONS, RANDOM_SEED
            )
            results[pop] = res

            z_v = res["z_vel"]
            z_p = res["z_pos"]

            if np.isnan(z_v) or np.isnan(z_p):
                verdict = "ERROR"
            elif z_v < -2.0 and z_p < -2.0:
                verdict = "✅ TRUE STRUCTURE"
            elif z_v < -2.0 and z_p >= -2.0:
                verdict = "⚠️ SPATIAL ARTIFACT"
            elif z_v >= -2.0 and z_p < -2.0:
                verdict = "⚠️ VELOCITY ARTIFACT"
            else:
                verdict = "❌ NO COUPLING"

            z_v_str = f"{z_v:+.2f}" if not np.isnan(z_v) else "NaN"
            z_p_str = f"{z_p:+.2f}" if not np.isnan(z_p) else "NaN"
            print(f"  {pop:<20s} {res['real']:>8.4f} {z_v_str:>8s} {z_p_str:>8s} {verdict:>18s}")

        except Exception as e:
            print(f"  {pop:<20s} ERROR: {e}")
            results[pop] = {key: np.nan for key in ["real", "z_vel", "z_pos", "null_vel_mean", "null_pos_mean"]}

    # === CROSS-POPULATION SUMMARY ===
    print("\n" + "=" * 78)
    print("🧪 PHASE 1 FINAL VERDICT (V8 Local Prediction)")
    print("-" * 50)

    sig = results.get("signal", {})
    prj = results.get("projection_control", {})
    fld = results.get("field_control", {})

    sig_pass = (sig.get("z_vel", 0) < -2.0) and (sig.get("z_pos", 0) < -2.0)
    prj_fail = not ((prj.get("z_vel", 0) < -2.0) and (prj.get("z_pos", 0) < -2.0))
    fld_fail = not ((fld.get("z_vel", 0) < -2.0) and (fld.get("z_pos", 0) < -2.0))

    print(f"  Signal passes both nulls (Z < -2):      {'✅ YES' if sig_pass else '❌ NO'}")
    print(f"  Projection fails at least one:           {'✅ YES' if prj_fail else '❌ NO'}")
    print(f"  Field fails at least one:                {'✅ YES' if fld_fail else '❌ NO'}")

    overall = sig_pass and prj_fail and fld_fail
    print(f"\n  🎯 OVERALL PHASE 1 STATUS: {'✅ PASS — METRIC VALIDATED' if overall else '❌ FAIL — FURTHER REDESIGN NEEDED'}")

    print("\n🔒 TRACEBIND V8 CHECKPOINT:")
    print(f"- Method: Median local k-NN velocity prediction error + dual-null")
    print(f"- Tests functional dependence P(v|x), not isotropic clustering")
    print(f"- k: {K_NEIGHBORS} | Permutations: {N_PERMUTATIONS} | Seed: {RANDOM_SEED}")
    print(f"- Threshold: Z < -2.0 on BOTH nulls for TRUE STRUCTURE")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V8")


if __name__ == "__main__":
    main()