"""Plot subsample R distributions with mean-consistent annotations and raw data overlay."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "reference")

REPLICATES_FILE = os.path.join(DATA_DIR, "tracebind_v11_subsample_replicates.csv")
SUMMARY_FILE = os.path.join(DATA_DIR, "tracebind_v11_subsample_summary.csv")


def main():
    reps = pd.read_csv(REPLICATES_FILE)
    summary = pd.read_csv(SUMMARY_FILE)

    # Verify 'fraction' column exists
    primary_frac = 0.80
    if "fraction" not in reps.columns:
        raise KeyError(
            f"'fraction' column not found in {REPLICATES_FILE}. "
            "Please rerun compute_subsample_stability.py which saves this column."
        )

    plot_data = reps[reps["fraction"] == primary_frac].copy()
    plot_data["Cluster"] = plot_data["cluster"].str.upper()

    # Build observed value lookup from summary table
    obs_lookup = {}
    for _, row in summary.iterrows():
        obs_lookup[row["cluster"]] = row["r_observed"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    ple_r = plot_data[plot_data["cluster"] == "pleiades"]["R"].values
    hya_r = plot_data[plot_data["cluster"] == "hyades"]["R"].values

    # Empirical dominance (descriptive; no independence assumption)
    emp_dominance = np.mean(hya_r[:, None] < ple_r[None, :])

    for ax, cluster_name, r_vals in zip(axes, ["pleiades", "hyades"], [ple_r, hya_r]):
        subset = plot_data[plot_data["cluster"] == cluster_name]
        n_subs = len(subset)
        if n_subs == 0:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
            continue

        # Violin without inner quartiles (raw points shown via stripplot)
        sns.violinplot(data=subset, y="R", color="#2E86AB", inner=None, ax=ax, width=0.6)

        # Jittered stripplot showing actual replicate values
        sns.stripplot(
            data=subset, y="R", color="black", alpha=0.22,
            size=2, jitter=0.18, ax=ax
        )

        r_obs = obs_lookup.get(cluster_name, np.nan)
        mean_sub = subset["R"].mean()
        sd_sub = subset["R"].std(ddof=1)
        se_mean = sd_sub / np.sqrt(n_subs)  # Computed but NOT displayed on figure
        q025, q975 = subset["R"].quantile([0.025, 0.975])
        cv = sd_sub / mean_sub if mean_sub > 0 else np.nan
        shift = mean_sub - r_obs if not np.isnan(r_obs) else np.nan
        rel_shift = 100 * shift / r_obs if not np.isnan(shift) else np.nan
        sk = skew(r_vals, bias=False)

        # Observed R (dashed magenta)
        if not np.isnan(r_obs):
            ax.axhline(y=r_obs, color="#A23B72", linestyle="--", linewidth=2.5,
                       label=f"Observed R = {r_obs:.4f}")

        # Subsample MEAN (dash-dot orange) — consistent with shift calculation
        ax.axhline(y=mean_sub, color="#F18F01", linestyle="-.", linewidth=2.5,
                   label=f"Subsample mean = {mean_sub:.4f}")

        # 95% subsampling interval (dotted gray)
        ax.axhline(y=q025, color="gray", linestyle=":", alpha=0.7)
        ax.axhline(y=q975, color="gray", linestyle=":", alpha=0.7,
                   label=f"95% subsampling interval [{q025:.4f}, {q975:.4f}]")

        # Shift annotation with relative percentage
        if not np.isnan(shift):
            ax.text(0.02, 0.97, f"Subsampling shift = {shift:+.4f} ({rel_shift:+.1f}%)",
                    transform=ax.transAxes, va="top", fontsize=10, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

        # Clean two-line title (SE and median excluded from figure)
        ax.set_title(
            f"{cluster_name.upper()}\n"
            f"N = {n_subs}   SD = {sd_sub:.4f}\n"
            f"CV = {cv:.4f}   Skew = {sk:+.3f}"
        )
        ax.set_ylabel("Coherence Ratio R")
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(axis="y", alpha=0.3)

    # Dynamic figure-level annotation using computed value
    fig.text(0.5, 0.01,
             "Across all pairwise comparisons between 80% subsample replicates, "
             f"the Hyades coherence ratio was lower than the Pleiades coherence ratio "
             f"in {100 * emp_dominance:.1f}% of cases.",
             ha="center", fontsize=11, style="italic")

    plt.suptitle("Empirical Stability of TRACEBIND-V11 Coherence Ratio", fontsize=14, y=1.02)
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])

    out_path = os.path.join(DATA_DIR, "tracebind_v11_subsample_distributions.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"💾 Plot saved to {out_path}")
    print(f"📊 Empirical dominance P(R_Hya < R_Ple) = {emp_dominance:.3f}")
    print(f"📊 Pleiades: SD={np.std(ple_r, ddof=1):.4f}, SE(mean)={np.std(ple_r, ddof=1)/np.sqrt(len(ple_r)):.4f}, "
          f"skew={skew(ple_r, bias=False):+.3f}, shift={np.mean(ple_r)-obs_lookup['pleiades']:+.4f} ({100*(np.mean(ple_r)-obs_lookup['pleiades'])/obs_lookup['pleiades']:+.1f}%)")
    print(f"📊 Hyades:   SD={np.std(hya_r, ddof=1):.4f}, SE(mean)={np.std(hya_r, ddof=1)/np.sqrt(len(hya_r)):.4f}, "
          f"skew={skew(hya_r, bias=False):+.3f}, shift={np.mean(hya_r)-obs_lookup['hyades']:+.4f} ({100*(np.mean(hya_r)-obs_lookup['hyades'])/obs_lookup['hyades']:+.1f}%)")
    plt.show()


if __name__ == "__main__":
    main()