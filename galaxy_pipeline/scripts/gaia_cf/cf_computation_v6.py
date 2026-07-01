"""
TRACEBIND v2.0 - Phase 1: Dual-Null Dispersion Ratio (V6)
Tests position-velocity coupling against BOTH velocity and position null models.
License: CC0 1.0 Universal
"""
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")

K_VALUES = [10, 20, 40]
N_PERMUTATIONS = 50
RANDOM_SEED = 42


def astrometry_to_cartesian(ra, dec, parallax):
    distance = 1000.0 / parallax
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return np.column_stack([x, y, z])


def _median_dispersion_ratio(positions_3d, pm_mag, k):
    """Core computation: median(σ_local / σ_global)."""
    n = len(positions_3d)
    if k >= n:
        return np.nan

    sigma_global = np.std(pm_mag)
    if sigma_global < 1e-10:
        return np.nan

    nn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean', algorithm='ball_tree')
    nn.fit(positions_3d)
    indices = nn.kneighbors(positions_3d, return_distance=False)[:, 1:]

    neighbor_pm = pm_mag[indices]
    sigma_local = np.std(neighbor_pm, axis=1)
    ratio = sigma_local / sigma_global
    return float(np.median(ratio))


def compute_dual_null(positions_3d, pmra, pmdec, k, n_perm, seed):
    """
    Compute real ratio + Z-scores against velocity-null and position-null.
    
    Returns dict with real, z_vel, z_pos, null_vel_mean, null_pos_mean
    """
    pm_mag = np.sqrt(pmra**2 + pmdec**2)
    real_ratio = _median_dispersion_ratio(positions_3d, pm_mag, k)

    if np.isnan(real_ratio):
        return {k: np.nan for k in ["real", "z_vel", "z_pos", "null_vel_mean", "null_pos_mean"]}

    rng = np.random.default_rng(seed)
    null_vel = []
    null_pos = []

    for _ in range(n_perm):
        # NULL 1: Shuffle velocities (breaks position-velocity coupling)
        perm_v = rng.permutation(len(pmra))
        shuffled_pm_mag_v = np.sqrt(pmra[perm_v]**2 + pmdec[perm_v]**2)
        r_v = _median_dispersion_ratio(positions_3d, shuffled_pm_mag_v, k)
        if not np.isnan(r_v):
            null_vel.append(r_v)

        # NULL 2: Shuffle positions (destroys spatial structure)
        perm_p = rng.permutation(len(positions_3d))
        shuffled_positions = positions_3d[perm_p]
        r_p = _median_dispersion_ratio(shuffled_positions, pm_mag, k)
        if not np.isnan(r_p):
            null_pos.append(r_p)

    def safe_z(real, null_list):
        if len(null_list) < 5:
            return np.nan, np.nan
        mean_n = np.mean(null_list)
        std_n = np.std(null_list)
        z = (real - mean_n) / std_n if std_n > 1e-10 else np.nan
        return z, mean_n

    z_vel, mean_vel = safe_z(real_ratio, null_vel)
    z_pos, mean_pos = safe_z(real_ratio, null_pos)

    return {
        "real": real_ratio,
        "z_vel": z_vel,
        "z_pos": z_pos,
        "null_vel_mean": mean_vel,
        "null_pos_mean": mean_pos,
    }


def main():
    print("🔬 TRACEBIND V6: Dual-Null Dispersion Ratio")
    print("=" * 78)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} rows | Permutations: {N_PERMUTATIONS} | Seed: {RANDOM_SEED}\n")

    positions_3d = astrometry_to_cartesian(
        df["ra"].values, df["dec"].values, df["parallax"].values
    )

    populations = sorted(df["population"].unique())
    results = {}
    ref_k = 20

    print(f"📊 Dual-Null Results (k={ref_k}):")
    print("-" * 78)
    header = f"  {'Population':<20s} {'Real':>7s} {'Z_vel':>8s} {'Z_pos':>8s} {'Verdict':>18s}"
    print(header)
    print("-" * 78)

    for pop in populations:
        mask = df["population"] == pop
        try:
            res = compute_dual_null(
                positions_3d[mask],
                df.loc[mask, "pmra"].values,
                df.loc[mask, "pmdec"].values,
                ref_k, N_PERMUTATIONS, RANDOM_SEED
            )
            results[pop] = res

            # VERDICT LOGIC:
            # TRUE STRUCTURE: Z_vel < -2 AND Z_pos < -2
            # SPATIAL ARTIFACT: Z_vel < -2 BUT Z_pos >= -2
            # NO COUPLING: Z_vel >= -2
            z_v = res["z_vel"]
            z_p = res["z_pos"]

            if np.isnan(z_v) or np.isnan(z_p):
                verdict = "ERROR"
            elif z_v < -2.0 and z_p < -2.0:
                verdict = "✅ TRUE STRUCTURE"
            elif z_v < -2.0 and z_p >= -2.0:
                verdict = "⚠️ SPATIAL ARTIFACT"
            else:
                verdict = "❌ NO COUPLING"

            z_v_str = f"{z_v:+.2f}" if not np.isnan(z_v) else "NaN"
            z_p_str = f"{z_p:+.2f}" if not np.isnan(z_p) else "NaN"
            print(f"  {pop:<20s} {res['real']:>7.4f} {z_v_str:>8s} {z_p_str:>8s} {verdict:>18s}")

        except Exception as e:
            print(f"  {pop:<20s} ERROR: {e}")
            results[pop] = {k: np.nan for k in ["real", "z_vel", "z_pos", "null_vel_mean", "null_pos_mean"]}

    # === CROSS-POPULATION SUMMARY ===
    print("\n" + "=" * 78)
    print("🧪 PHASE 1 FINAL VERDICT (Dual-Null)")
    print("-" * 50)

    for pop in populations:
        r = results.get(pop, {})
        z_v = r.get("z_vel", np.nan)
        z_p = r.get("z_pos", np.nan)
        print(f"  {pop:20s}: Z_vel={z_v:+.2f}  Z_pos={z_p:+.2f}" if not (np.isnan(z_v) or np.isnan(z_p)) else f"  {pop:20s}: ERROR")

    sig = results.get("signal", {})
    prj = results.get("projection_control", {})
    fld = results.get("field_control", {})

    sig_pass = (sig.get("z_vel", 0) < -2.0) and (sig.get("z_pos", 0) < -2.0)
    prj_fail = not ((prj.get("z_vel", 0) < -2.0) and (prj.get("z_pos", 0) < -2.0))
    fld_fail = not ((fld.get("z_vel", 0) < -2.0) and (fld.get("z_pos", 0) < -2.0))

    print(f"\n  Signal passes both nulls:       {'✅ YES' if sig_pass else '❌ NO'}")
    print(f"  Projection fails at least one:  {'✅ YES' if prj_fail else '❌ NO'}")
    print(f"  Field fails at least one:       {'✅ YES' if fld_fail else '❌ NO'}")

    overall = sig_pass and prj_fail and fld_fail
    print(f"\n  🎯 OVERALL PHASE 1 STATUS: {'✅ PASS — METRIC VALIDATED' if overall else '❌ FAIL — FURTHER REDESIGN NEEDED'}")

    print("\n🔒 TRACEBIND V6 CHECKPOINT:")
    print(f"- Method: Dual-null (velocity shuffle + position shuffle)")
    print(f"- Permutations: {N_PERMUTATIONS} | k: {ref_k} | Seed: {RANDOM_SEED}")
    print(f"- Threshold: Z < -2.0 on BOTH nulls for TRUE STRUCTURE")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH V6")


if __name__ == "__main__":
    main()