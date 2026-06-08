import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import ks_2samp

def plot_anatomy_from_master():
    input_file = 'data/tracebind_master_catalog_v1.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}. Run build_master_catalog.py first.")
        return

    df = pd.read_csv(input_file)
    
    # Isolate the High-Tension Benchmark Population
    bench = df[df['anomaly_class'] != 'Below Top 5% Threshold'].copy()
    
    color_map = {
        'Faint Star Noise Suspect (G > 14.5)': 'mediumpurple',
        'Bright Star Artifact Suspect (G < 6)': 'darkorange',
        'Known NSS Orbit (Binary/Multiple)': 'royalblue',
        'NSS Acceleration (PMa / Unseen Companion)': 'limegreen',
        'Unexplained Astrometric Tension (High Priority)': 'crimson'
    }
    plot_order = list(color_map.keys())
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle('TRACEBIND Phase 11B: Anatomy of the Master Catalog Anomalies', 
                 fontsize=18, fontweight='bold', y=0.98)

    def plot_classes(ax, x_col, y_col, x_label, y_label, title, invert_x=False, invert_y=False, x_lim=None):
        for cls in plot_order:
            subset = bench[bench['anomaly_class'] == cls]
            plot_data = subset.dropna(subset=[x_col, y_col])
            if plot_data.empty: continue
            
            alpha = 0.8 if cls == 'Unexplained Astrometric Tension (High Priority)' else 0.4
            s = 40 if cls == 'Unexplained Astrometric Tension (High Priority)' else 20
            
            ax.scatter(plot_data[x_col], plot_data[y_col], c=color_map[cls], 
                       s=s, alpha=alpha, label=cls, edgecolors='none')
            
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.4)
        if invert_x: ax.invert_xaxis()
        if invert_y: ax.invert_yaxis()
        if x_lim: ax.set_xlim(x_lim)

    # 1. HR Diagram
    plot_classes(axes[0, 0], 'bp_rp', 'M_G', 'Gaia BP-RP Color', 'Absolute Magnitude (M_G)', 
                 'Hertzsprung-Russell Diagram', invert_y=True)
    # 2. Discovery Quadrant
    plot_classes(axes[0, 1], 'ruwe', 'astrometric_excess_noise', 'RUWE', 'Excess Noise (mas)', 
                 'The Discovery Quadrant')
    # 3. Galactic Latitude
    plot_classes(axes[1, 0], 'gal_b', 'tension_score', 'Galactic Latitude (b)', 'Tension Score', 
                 'Galactic Crowding vs. Tension')
    # 4. Teff vs Tension
    plot_classes(axes[1, 1], 'teff_gspphot', 'tension_score', 'Effective Temperature (K)', 'Tension Score', 
                 'Stellar Activity / Teff vs. Tension', invert_x=True)
    # 5. Kinematics
    plot_classes(axes[2, 0], 'vt_kms', 'tension_score', 'Tangential Velocity (km/s)', 'Tension Score', 
                 'Kinematics vs. Tension', x_lim=(0, 250))
    # 6. Distance
    plot_classes(axes[2, 1], 'distance_pc', 'tension_score', 'Distance (pc)', 'Tension Score', 
                 'Distance vs. Tension', x_lim=(0, 55))

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=3, fontsize=12, 
               bbox_to_anchor=(0.5, -0.02), frameon=True)

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    os.makedirs('figures', exist_ok=True)
    plt.savefig('figures/phase11b_anatomy_master.png', dpi=300, bbox_inches='tight')
    print("✅ Saved Anatomy Plot to figures/phase11b_anatomy_master.png\n")

    # KS Tests
    unknowns = bench[bench['anomaly_class'] == 'Unexplained Astrometric Tension (High Priority)']
    explained = bench[bench['anomaly_class'] != 'Unexplained Astrometric Tension (High Priority)']
    
    print("="*85)
    print("KOLMOGOROV-SMIRNOV TESTS: Unknowns vs. Explained")
    print("="*85)
    for name, col in [('BP-RP Color', 'bp_rp'), ('Distance', 'distance_pc'), ('Teff', 'teff_gspphot')]:
        u_data = unknowns[col].dropna()
        e_data = explained[col].dropna()
        if len(u_data) > 0 and len(e_data) > 0:
            stat, p = ks_2samp(u_data, e_data)
            print(f"{name:<15} | p-value: {p:.2e} | {'✅ DISTINCT' if p < 0.05 else '❌ CONSISTENT'}")
    print("="*85)

if __name__ == "__main__":
    plot_anatomy_from_master()