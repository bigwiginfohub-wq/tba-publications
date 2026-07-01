"""
Plot TRACEBIND Purity Calibration Curve (Two-Panel Publication Figure).
License: CC0 1.0 Universal
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up TWO levels: gaia_cf -> scripts -> GaiaProject
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "real")
CSV_FILE = os.path.join(OUTPUT_DIR, "purity_calibration_final.csv")

# Observed Hyades Baseline from Benchmark
OBSERVED_HYADES_MEDIAN = 0.8499

def main():
    if not os.path.exists(CSV_FILE):
        raise RuntimeError(f"Calibration file not found: {CSV_FILE}. Run run_purity_sweep.py first.")
        
    df = pd.read_csv(CSV_FILE)
    df = df.sort_values("contamination")
    
    # Create Two-Panel Figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    x = df["contamination"] * 100
    
    # --- Panel 1: Median Ratio with Shaded CI ---
    ax1.plot(x, df["cluster_mean"], marker='o', color='#2E86AB', linewidth=2, label='Cluster Median (R)')
    ax1.fill_between(x, df["cluster_ci_lower"], df["cluster_ci_upper"], alpha=0.2, color='#2E86AB')
    
    # Field Baseline with Uncertainty
    field_mean = df["field_mean"].mean()
    # Approximate field CI from the data (or use a fixed value if known)
    field_std = df["field_mean"].std() 
    ax1.axhline(y=field_mean, color='#A23B72', linestyle='--', linewidth=1.5, label='Field Baseline')
    ax1.fill_between([0, 100], field_mean - field_std, field_mean + field_std, alpha=0.1, color='#A23B72')
    
    # Annotate Observed Hyades
    ax1.scatter([0], [OBSERVED_HYADES_MEDIAN], color='gold', s=100, zorder=5, edgecolors='black', label=f'Observed Hyades ({OBSERVED_HYADES_MEDIAN:.3f})')
    
    ax1.set_ylabel('Median Ratio (R)', fontsize=12)
    ax1.set_title('TRACEBIND V11 Sensitivity to Membership Contamination\n(5 Master Seeds × 30 Realizations per level)', fontsize=13)
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0.8, 1.05)

    # --- Panel 2: Separation Frequency ---
    ax2.bar(x, df["separation_freq"] * 100, color='#F18F01', alpha=0.8, width=15)
    ax2.set_xlabel('Membership Contamination (%)', fontsize=12)
    ax2.set_ylabel('Separation Freq. (%)', fontsize=11)
    ax2.set_ylim(0, 105)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(df["separation_freq"] * 100):
        ax2.text(x[i], v + 2, f'{v:.0f}%', ha='center', fontsize=9)

    plt.tight_layout()
    
    # Save Plot
    plot_path = os.path.join(OUTPUT_DIR, "purity_calibration_figure.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"✅ Publication figure saved to {plot_path}")

if __name__ == "__main__":
    main()