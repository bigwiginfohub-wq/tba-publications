import pandas as pd
import numpy as np
import os
from itertools import product

def run_coefficient_sweep():
    input_file = 'data/phase9_allsky_coherence_map.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} sky pixels for Coefficient Sensitivity Sweep.\n")

    # 1. Reconstruct normalized variables
    df['rho_norm'] = df['star_count'] / df['star_count'].max()
    df['interaction'] = df['rho_norm'] * df['cf']
    
    # 2. Define the Parameter Grid (Morpheus's Recommendation)
    alphas = [0.05, 0.10, 0.20]
    betas  = [0.05, 0.10, 0.20]
    gammas = [0.01, 0.05, 0.10]
    
    sweep_results = []
    
    # 3. Run the Sweep
    for a, b, g in product(alphas, betas, gammas):
        # Calculate M for this specific universe
        M = (a * df['rho_norm']) + (b * df['cf']) + (g * df['interaction'])
        
        # Calculate Phase Angle (theta) and Divergence (Delta A)
        theta_rad = np.arctan(M)
        theta_deg = np.degrees(theta_rad)
        
        A_lin = 1 + M
        A_quad = np.sqrt(1 + M**2)
        delta_A = A_lin - A_quad
        
        # Calculate correlations for this specific universe
        corr_cf = df['cf'].corr(theta_deg)
        corr_rho = df['rho_norm'].corr(theta_deg)
        corr_int = df['interaction'].corr(theta_deg)
        
        # Determine which term has the highest correlation with theta
        correlations = {'Cf': corr_cf, 'rho': corr_rho, 'Interaction': corr_int}
        dominant_driver = max(correlations, key=correlations.get)
        
        sweep_results.append({
            'alpha': a, 'beta': b, 'gamma': g,
            'max_M': M.max(),
            'max_theta_deg': theta_deg.max(),
            'mean_theta_deg': theta_deg.mean(),
            'max_delta_A': delta_A.max(),
            'corr_cf': corr_cf,
            'corr_rho': corr_rho,
            'corr_int': corr_int,
            'dominant_driver': dominant_driver
        })
        
    sweep_df = pd.DataFrame(sweep_results)
    
    # 4. Analyze the Sweep Results
    interaction_wins = (sweep_df['dominant_driver'] == 'Interaction').sum()
    total_tests = len(sweep_df)
    win_pct = (interaction_wins / total_tests) * 100
    
    print("="*85)
    print("      COEFFICIENT SENSITIVITY SWEEP RESULTS")
    print("="*85)
    print(f"Tested {total_tests} unique parameter combinations (α, β, γ).\n")
    
    print("Question: Is the Interaction term structurally dominant?")
    print(f"   Interaction drove θ in {interaction_wins}/{total_tests} scenarios ({win_pct:.1f}%).")
    
    if win_pct == 100.0:
        print("   ✅ ABSOLUTE STRUCTURAL DOMINANCE.")
        print("   Regardless of how the weights are tuned, the collision of high density")
        print("   and high coherence (ρ × Cf) is the mathematical engine of the phase shift.")
    elif win_pct >= 80.0:
        print("   ✅ STRONG STRUCTURAL DOMINANCE.")
        print("   The interaction term is the primary driver in the vast majority of parameter spaces.")
    else:
        print("   ⚠️ PARAMETER FRAGILITY DETECTED.")
        print("   The dominant driver shifts depending on the exact weights chosen.")

    print("\n--- EXTREME SCENARIOS (Highest Phase Angles) ---")
    top_scenarios = sweep_df.sort_values('max_theta_deg', ascending=False).head(5)
    print(f"{'α':>4} | {'β':>4} | {'γ':>4} | {'Max M':>6} | {'Max θ (deg)':>11} | {'Max ΔA':>8} | {'Driver':<12}")
    print("-" * 65)
    for idx, row in top_scenarios.iterrows():
        print(f"{row['alpha']:>4.2f} | {row['beta']:>4.2f} | {row['gamma']:>4.2f} | {row['max_M']:>6.3f} | {row['max_theta_deg']:>11.2f} | {row['max_delta_A']:>8.4f} | {row['dominant_driver']:<12}")

    # Save
    out_file = 'data/sandbox_coefficient_sweep_results.csv'
    sweep_df.to_csv(out_file, index=False)
    print(f"\n💾 Saved full sweep matrix to: {out_file}")
    print("="*85)

if __name__ == "__main__":
    run_coefficient_sweep()