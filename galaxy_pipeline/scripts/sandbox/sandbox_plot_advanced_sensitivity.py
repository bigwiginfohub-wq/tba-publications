import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_advanced_interaction_impact():
    input_file = 'data/sandbox_coefficient_sweep_results.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}. Please run the sweep first.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} sweep scenarios for advanced plotting.\n")

    # Fix 4: Reproducible Jitter
    np.random.seed(42) 
    
    # Fix 5: Statistical Tests
    corr_max = df['gamma'].corr(df['max_theta_deg'])
    corr_mean = df['gamma'].corr(df['mean_theta_deg'])
    print(f"📊 Correlation (γ vs Max θ) : {corr_max:.3f}")
    print(f"📊 Correlation (γ vs Mean θ): {corr_mean:.3f}\n")

    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Fix 1: Color-code by β, Size by α
    betas = sorted(df['beta'].unique())
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(betas))) # Use viridis colormap
    
    for i, beta in enumerate(betas):
        subset = df[df['beta'] == beta]
        x_jitter = np.random.normal(0, 0.002, size=len(subset))
        
        # Scale alpha to be visible as marker size
        sizes = subset['alpha'] * 1000 
        
        ax.scatter(
            subset['gamma'] + x_jitter, 
            subset['max_theta_deg'], 
            s=sizes, 
            c=[colors[i]], 
            alpha=0.75, 
            edgecolors='black', 
            linewidth=0.8,
            label=f'β = {beta:.2f} (Coherence)'
        )
        
    # Fix 2: Plot the Mean Trend to counter the "Extreme Value" instability
    gamma_means = df.groupby('gamma')['mean_theta_deg'].mean()
    ax.plot(gamma_means.index, gamma_means.values, 'r--', linewidth=3, 
            marker='o', markersize=8, label='Mean θ (Structural Trend)', zorder=5)

    # Fix 3: Softened, Accurate Title
    ax.set_title('Phase Rotation Sensitivity to Interaction Weight γ\n(Visualizing α as Size, β as Color)', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Interaction Weight (γ)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Phase Angle θ (degrees)', fontsize=13, fontweight='bold')
    
    ax.set_xticks([0.01, 0.05, 0.10])
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # Legend
    ax.legend(title="Model Parameters", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)

    # Fix 5: Annotate Statistics
    stats_text = f"Pearson r (γ vs Max θ) : {corr_max:.3f}\nPearson r (γ vs Mean θ): {corr_mean:.3f}"
    ax.text(0.04, 23, stats_text, fontsize=11, family='monospace',
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='black', boxstyle='round,pad=0.5'))

    # Epistemological Caveat (Reviewer's mandate)
    caveat_text = "⚠️ Note: This characterizes the toy model's geometry,\nnot a physical astrophysical law."
    ax.text(0.04, 2, caveat_text, fontsize=10, color='darkred', fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='darkred', boxstyle='round,pad=0.5'))

    plt.tight_layout()
    
    # Save
    os.makedirs('figures', exist_ok=True)
    out_path = 'figures/sandbox_advanced_theta_vs_gamma.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✅ Publication-grade plot saved to {out_path}")
    plt.show()

if __name__ == "__main__":
    plot_advanced_interaction_impact()