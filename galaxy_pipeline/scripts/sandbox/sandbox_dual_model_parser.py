import pandas as pd
import numpy as np
import os

def analyze_allsky_amplification(alpha=0.1, beta=0.1, gamma=0.05):
    input_file = 'data/phase9_allsky_coherence_map.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}. Please run your Phase 9 mapping script first.")
        return

    # Load your mapped sky pixels
    sky_map = pd.read_csv(input_file)
    print(f"📋 Loaded {len(sky_map)} sky pixels from Phase 9 telemetry.")

    # 1. Approximate localized densities (rho) for the sky map
    # Using star count as a normalized proxy for the theoretical model
    sky_map['rho_proxy'] = sky_map['star_count'] / sky_map['star_count'].max()
    sky_map['rho_norm'] = sky_map['rho_proxy']  

    # 2. Compute the shared modification term: (α*ρ_norm + β*Cf + γ*ρ_norm*Cf)
    sky_map['modification'] = (alpha * sky_map['rho_norm'] + 
                               beta * sky_map['cf'] + 
                               gamma * sky_map['rho_norm'] * sky_map['cf'])

    # 3. Calculate both Amplification Modes
    # Linear: Forces act in the exact same direction (collinear)
    sky_map['A_linear'] = 1 + sky_map['modification']
    
    # Quadrature: Forces act at right angles to each other (orthogonal vectors)
    sky_map['A_quadrature'] = np.sqrt(1 + sky_map['modification']**2)

    # 4. Compute the exact divergence drop percentage
    # Measures how much amplification is lost if switching from linear to quadrature
    sky_map['force_loss_pct'] = ((sky_map['A_linear'] - sky_map['A_quadrature']) / sky_map['A_linear']) * 100

    # Sort by force loss to see where the geometric assumption alters the math the most
    sky_map = sky_map.sort_values('force_loss_pct', ascending=False)

    print("\n" + "="*75)
    print("      DIVERGENCE REPORT: LINEAR MODEL VS. QUADRATURE SUPPRESSION")
    print("="*75)
    print(f"{'Pixel ID':<10} | {'Stars':>6} | {'Cf':>8} | {'A (Linear)':>12} | {'A (Quadrature)':>14} | {'Force Loss %':>12}")
    print("-" * 75)
    
    # Display the top 10 regions experiencing maximum model divergence
    for idx, row in sky_map.head(10).iterrows():
        print(f"{int(row['pixel_id']):<10} | {int(row['star_count']):>6} | {row['cf']:>8.4f} | {row['A_linear']:>12.4f} | {row['A_quadrature']:>14.4f} | {row['force_loss_pct']:>11.2f}%")

    # Save comparative data to disk
    output_comparison_file = 'data/sandbox_model_comparison.csv'
    sky_map.to_csv(output_comparison_file, index=False)
    print("\n" + "="*75)
    print(f"💾 Saved complete dual-model comparison matrix to: {output_comparison_file}")
    print("="*75)

if __name__ == "__main__":
    # Evaluates the map using your theoretical parameters
    analyze_allsky_amplification(alpha=0.1, beta=0.1, gamma=0.05)