"""TRACEBIND-V11: True Influence Analysis via Leave-One-Out R Perturbation."""
import pandas as pd
import numpy as np
import os
import time
from tracebind_v11_core import (
    astrometry_to_tangential_velocity,
    build_neighbor_graph,
    compute_loo_prediction_error,
    compute_own_geometry_baseline,
    EPSILON
)

# ===== CONFIGURATION =====
K_PREDICT = 30
K_SHUFFLE = 50
N_PERMUTATIONS = 1000
NOISE_FRACTION = 0.10
RANDOM_SEED = 42
TOP_N_INFLUENTIAL = [5, 10, 20]
CHECKPOINT_INTERVAL = 1  # Save after every star; negligible I/O cost per iteration

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")
CLUSTERS = ["hyades"]


def run_tracebind(df, k, noise_frac, seed, n_permutations):
    """Run V11 pipeline. Returns R and median prediction error."""
    df = df.dropna(subset=["ra", "dec", "parallax", "pmra", "pmdec"]).copy()
    df = df[df["parallax"] > 0].copy()
    if len(df) <= k:
        return {"R": np.nan, "E_real": np.nan}

    pos_3d, vel_vec = astrometry_to_tangential_velocity(
        df["ra"].values, df["dec"].values, df["parallax"].values,
        df["pmra"].values, df["pmdec"].values
    )
    max_k = max(k, K_SHUFFLE) + 1
    graph = build_neighbor_graph(pos_3d, max_k)
    real_err = compute_loo_prediction_error(vel_vec, k, graph)
    null_errors = compute_own_geometry_baseline(
        vel_vec, k, K_SHUFFLE, n_permutations, seed, noise_frac, graph
    )
    baseline_mean = np.mean(null_errors)
    ratio = real_err / baseline_mean if baseline_mean > 1e-12 else np.nan
    return {"R": ratio, "E_real": real_err}


def load_or_initialize_checkpoint(cluster):
    """Load existing checkpoint or create new one. Resume by star_index, not row position."""
    ckpt_path = os.path.join(DATA_DIR, f"tracebind_v11_influence_{cluster}_checkpoint.csv")
    if os.path.exists(ckpt_path):
        ckpt_df = pd.read_csv(ckpt_path)
        completed_indices = set(ckpt_df["star_index"].astype(int).tolist())
        print(f"   📂 Resuming {cluster.upper()}: {len(completed_indices)} stars completed")
        return ckpt_df, completed_indices
    else:
        cols = ["star_index", "delta_R_signed", "delta_R_abs", 
                "R_after", "E_real_after", "source_id", "ruwe", "aen", "phot_g_mean_mag"]
        return pd.DataFrame(columns=cols), set()


def save_checkpoint(ckpt_df, cluster):
    """Save checkpoint directly to avoid Windows file-locking errors."""
    ckpt_path = os.path.join(DATA_DIR, f"tracebind_v11_influence_{cluster}_checkpoint.csv")
    # Direct overwrite avoids WinError 5 if the file is briefly touched by Excel/OneDrive
    ckpt_df.to_csv(ckpt_path, index=False)


def format_elapsed(start_time, completed, total):
    """Format elapsed time and estimate remaining with correct units."""
    elapsed = time.time() - start_time
    rate = elapsed / max(completed, 1)
    remaining = rate * (total - completed)
    
    def fmt(seconds):
        h, remainder = divmod(int(seconds), 3600)
        m, s = divmod(remainder, 60)
        return f"{h}h {m}m {s}s"
    
    return f"Elapsed: {fmt(elapsed)} | Est. remaining: {fmt(remaining)}"


def main():
    print("🔬 TRACEBIND-V11: True Influence Analysis (Leave-One-Out R)")
    print("=" * 80)
    print(f"   Testing removal of top {TOP_N_INFLUENTIAL} most influential stars\n")

    all_star_metadata = []
    summary_results = []
    global_start = time.time()

    for cluster in CLUSTERS:
        input_file = os.path.join(DATA_DIR, f"{cluster}_cg22_dr3_crossmatched.csv")
        if not os.path.exists(input_file):
            continue

        df_original = pd.read_csv(input_file)
        
        # FIX #1 & #2: n_stars ALWAYS equals actual DataFrame length
        n_stars = len(df_original)

        # Baseline result
        baseline = run_tracebind(df_original, K_PREDICT, NOISE_FRACTION, RANDOM_SEED, N_PERMUTATIONS)
        r_base = baseline["R"]
        e_base = baseline["E_real"]

        print(f"📊 {cluster.upper()} (N={n_stars})")
        print(f"   Baseline: R = {r_base:.4f}, E_real = {e_base:.4f} km/s")

        # Build neighbor graph ONCE; reuse distances for spatial leverage diagnostics
        pos_3d, _ = astrometry_to_tangential_velocity(
            df_original["ra"].values, df_original["dec"].values, df_original["parallax"].values,
            df_original["pmra"].values, df_original["pmdec"].values
        )
        max_k = max(K_PREDICT, K_SHUFFLE) + 1
        graph = build_neighbor_graph(pos_3d, max_k)

        # Spatial leverage diagnostics using CACHED graph distances
        weights_per_star = np.zeros(n_stars)
        nn_distances = np.zeros((n_stars, K_PREDICT))
        for i in range(n_stars):
            dists = graph["distances"][i][:K_PREDICT]
            nn_distances[i] = dists
            weights_per_star[i] = np.sum(1.0 / (dists**2 + EPSILON))

        weight_ratio_to_median = weights_per_star / np.median(weights_per_star)
        print(f"\n   Spatial leverage stats:")
        print(f"      Median NN dist: {np.median(nn_distances):.4f} pc")
        print(f"      Weight / median: p95={np.percentile(weight_ratio_to_median, 95):.1f}×, "
              f"p99={np.percentile(weight_ratio_to_median, 99):.1f}×")

        # Load checkpoint with robust index-based resume
        ckpt_df, completed_indices = load_or_initialize_checkpoint(cluster)
        influence_scores = np.zeros(n_stars)
        if len(completed_indices) > 0:
            for _, row in ckpt_df.iterrows():
                idx = int(row["star_index"])
                influence_scores[idx] = abs(row["delta_R_signed"])

        # Efficient batch accumulation for checkpointing
        pending_rows = []
        cluster_start = time.time()

        try:
            for i in range(n_stars):
                if i in completed_indices:
                    continue

                mask = np.ones(n_stars, dtype=bool)  # FIX #2: Mask matches full dataset length
                mask[i] = False
                df_loo = df_original[mask].reset_index(drop=True)
                
                loo_result = run_tracebind(df_loo, K_PREDICT, NOISE_FRACTION, RANDOM_SEED, N_PERMUTATIONS)
                
                r_after = loo_result["R"]
                e_after = loo_result["E_real"]
                signed_delta = r_after - r_base if not np.isnan(r_after) else 0.0
                influence_scores[i] = abs(signed_delta)

                row_data = df_original.iloc[i]
                pending_rows.append({
                    "star_index": i,
                    "delta_R_signed": signed_delta,
                    "delta_R_abs": abs(signed_delta),
                    "R_after": r_after if not np.isnan(r_after) else np.nan,
                    "E_real_after": e_after if not np.isnan(e_after) else np.nan,
                    "source_id": row_data.get("source_id", row_data.get("Source", np.nan)),
                    "ruwe": row_data.get("ruwe", np.nan),
                    "aen": row_data.get("aen", np.nan),
                    "phot_g_mean_mag": row_data.get("phot_g_mean_mag", row_data.get("G", np.nan))
                })

                # Atomic checkpoint at configured interval
                if len(pending_rows) >= CHECKPOINT_INTERVAL or i == n_stars - 1:
                    new_batch = pd.DataFrame(pending_rows)
                    ckpt_df = pd.concat([ckpt_df, new_batch], ignore_index=True)
                    save_checkpoint(ckpt_df, cluster)
                    pending_rows.clear()
                    
                    # FIX #3: Progress count uses unique star indices, not row count
                    current_completed = ckpt_df["star_index"].nunique()
                    timing = format_elapsed(cluster_start, current_completed, n_stars)
                    print(f"      💾 Checkpoint saved ({current_completed}/{n_stars}) | {timing}")

        except Exception as e:
            # Save any pending rows before re-raising
            if pending_rows:
                new_batch = pd.DataFrame(pending_rows)
                ckpt_df = pd.concat([ckpt_df, new_batch], ignore_index=True)
                save_checkpoint(ckpt_df, cluster)
            print(f"\n⚠️ Error at star {i}: {type(e).__name__}: {e}")
            print("   Checkpoint preserved. Rerun to resume.")
            raise

        # Rank by true influence on R
        influence_ranking = np.argsort(-influence_scores)

        # Collect top-20 metadata with safe lookup
        for rank_idx in range(min(20, n_stars)):
            orig_idx = influence_ranking[rank_idx]
            match = ckpt_df.loc[ckpt_df.star_index == orig_idx]
            
            # FIX #4: Guard against missing stars in checkpoint
            if len(match) == 0:
                continue
                
            meta_row = match.iloc[0].to_dict()
            meta_row["influence_rank"] = rank_idx + 1
            meta_row["cluster"] = cluster
            all_star_metadata.append(meta_row)

        # Influence test: remove top-N most influential stars
        row_summary = {"cluster": cluster, "n_stars": n_stars,
                       "baseline_R": r_base, "baseline_E": e_base}

        for top_n in TOP_N_INFLUENTIAL:
            mask = np.ones(n_stars, dtype=bool)  # FIX #2: Mask matches full dataset length
            mask[influence_ranking[:top_n]] = False
            df_reduced = df_original[mask].reset_index(drop=True)

            reduced = run_tracebind(df_reduced, K_PREDICT, NOISE_FRACTION,
                                    RANDOM_SEED, N_PERMUTATIONS)
            delta_r = reduced["R"] - r_base if not np.isnan(reduced["R"]) else np.nan
            delta_e = reduced["E_real"] - e_base if not np.isnan(reduced["E_real"]) else np.nan

            print(f"\n   Remove top {top_n} influential stars:")
            print(f"      R = {reduced['R']:.4f} (Δ = {delta_r:+.4f})")
            print(f"      E_real = {reduced['E_real']:.4f} km/s (Δ = {delta_e:+.4f})")

            row_summary[f"R_top{top_n}_removed"] = reduced["R"]
            row_summary[f"dR_top{top_n}"] = delta_r
            row_summary[f"dE_top{top_n}"] = delta_e

        summary_results.append(row_summary)
        print("\n" + "-" * 80)

    # Final outputs
    meta_df = pd.DataFrame(all_star_metadata)
    meta_path = os.path.join(DATA_DIR, "tracebind_v11_influential_stars_metadata.csv")
    meta_df.to_csv(meta_path, index=False)
    print(f"💾 High-influence star metadata saved to {meta_path}")

    sum_df = pd.DataFrame(summary_results)
    sum_path = os.path.join(DATA_DIR, "tracebind_v11_influence_summary.csv")
    sum_df.to_csv(sum_path, index=False)
    print(f"💾 Influence summary saved to {sum_path}")

    # Descriptive assessment
    print("\n📋 DESCRIPTIVE ASSESSMENT:")
    for row in summary_results:
        cluster = row["cluster"].upper()
        max_delta = max(abs(row.get(f"dR_top{n}", 0)) or 0 for n in TOP_N_INFLUENTIAL)
        print(f"   {cluster}: Removing the highest-influence stars changed R by at most "
              f"|ΔR| = {max_delta:.4f}.")


if __name__ == "__main__":
    main()