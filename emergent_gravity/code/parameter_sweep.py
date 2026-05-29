"""
Emergent Gravity Parameter Sweep

This script performs a full parameter sweep of the emergent gravity model:
    A = 1 + α·ρ_norm + β·Cf + γ·ρ_norm·Cf

Parameters:
    α (density amplification): 0 → 1 (step 0.1) → 11 values
    β (coherence amplification): 0 → 1 (step 0.1) → 11 values
    γ (density-coherence synergy): 0 → 0.5 (step 0.05) → 11 values
    ρ_norm (normalized density): 0.5 → 5 (step 0.5) → 10 values
    Cf (coherence factor): 0.0 (baseline) and 0.9 (full deployment)

Total combinations: 11 × 11 × 11 × 10 = 13,310

Outputs:
    - CSV file with all parameter combinations and amplification values
    - Plot of amplification vs Cf for three density levels
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
alpha_vals = np.arange(0, 1.1, 0.1)      # 0.0 to 1.0 step 0.1
beta_vals = np.arange(0, 1.1, 0.1)        # 0.0 to 1.0 step 0.1
gamma_vals = np.arange(0, 0.55, 0.05)     # 0.0 to 0.5 step 0.05
rho_vals = np.arange(0.5, 5.5, 0.5)       # 0.5 to 5.0 step 0.5
Cf_vals = [0.0, 0.9]                      # Baseline and full deployment

def amplification(rho, Cf, alpha, beta, gamma):
    """Compute amplification factor A"""
    return 1 + alpha * rho + beta * Cf + gamma * rho * Cf

# Run sweep
results = []
for alpha in alpha_vals:
    for beta in beta_vals:
        for gamma in gamma_vals:
            for rho in rho_vals:
                for Cf in Cf_vals:
                    A = amplification(rho, Cf, alpha, beta, gamma)
                    results.append({
                        'alpha': alpha,
                        'beta': beta,
                        'gamma': gamma,
                        'rho_norm': rho,
                        'Cf': Cf,
                        'amplification': A
                    })

df = pd.DataFrame(results)

# Save to CSV
csv_path = 'emergent_gravity_parameter_sweep.csv'
df.to_csv(csv_path, index=False)
print(f"Saved {len(results)} rows to {csv_path}")

# Print summary statistics
print("\n=== AMPLIFICATION RANGES ===")
for Cf in [0.0, 0.9]:
    subset = df[df['Cf'] == Cf]
    print(f"\nCf = {Cf}:")
    print(f"  Min amplification: {subset['amplification'].min():.3f}")
    print(f"  Max amplification: {subset['amplification'].max():.3f}")

# Compute parameter sensitivity (average amplification difference per unit change)
print("\n=== PARAMETER SENSITIVITY ===")
for param, vals in [('alpha', alpha_vals), ('beta', beta_vals), ('gamma', gamma_vals), ('rho_norm', rho_vals)]:
    if len(vals) > 1:
        step = vals[1] - vals[0]
        # Average change in amplification per unit change in parameter
        sensitivity = 0
        count = 0
        for Cf in [0.0, 0.9]:
            for p in vals[:-1]:
                subset_low = df[(df[param] == p) & (df['Cf'] == Cf)]
                subset_high = df[(df[param] == p + step) & (df['Cf'] == Cf)]
                delta_A = subset_high['amplification'].mean() - subset_low['amplification'].mean()
                sensitivity += delta_A / step
                count += 1
        sensitivity /= count
        print(f"  {param}: {sensitivity:.4f}")

# Generate amplification vs Cf plot for default coefficients
default_alpha, default_beta, default_gamma = 0.1, 0.2, 0.05
Cf_plot = np.linspace(0, 1, 100)
rho_plot_vals = [0.5, 2.0, 5.0]

plt.figure(figsize=(8, 6))
for rho in rho_plot_vals:
    A_plot = amplification(rho, Cf_plot, default_alpha, default_beta, default_gamma)
    plt.plot(Cf_plot, A_plot, label=f'ρ_norm = {rho}')

plt.xlabel('Coherence Factor (Cf)')
plt.ylabel('Amplification (A)')
plt.title(f'Emergent Gravity: Amplification vs Coherence\nα={default_alpha}, β={default_beta}, γ={default_gamma}')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()

plot_path = 'amplification_vs_cf.png'
plt.savefig(plot_path, dpi=150)
print(f"\nPlot saved to {plot_path}")
plt.show()