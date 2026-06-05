import pandas as pd
import numpy as np
import os

def run_euler_phase_analysis(alpha=0.1, beta=0.1, gamma=0.05):
    input_file = 'data/phase9_allsky_coherence_map.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} sky pixels for Euler Phase Analysis.\n")

    # 1. Reconstruct normalized variables and Modification term (M)
    df['rho_norm'] = df['star_count'] / df['star_count'].max()
    df['M'] = (alpha * df['rho_norm']) + (beta * df['cf']) + (gamma * df['rho_norm'] * df['cf'])
    
    # 2. Amplification Models
    # Linear: Purely real addition (A = 1 + M)
    df['A_linear'] = 1 + df['M']
    
    # Quadrature: The Magnitude of the complex vector |A| = sqrt(1^2 + M^2)
    df['A_quad'] = np.sqrt(1 + df['M']**2) 
    
    # 3. Euler's Formula / Complex Plane Diagnostics
    # Treat A as a complex number: 1 + iM
    # theta = arctan(Imaginary / Real) = arctan(M / 1)
    df['theta_rad'] = np.arctan(df['M'])
    df['theta_deg'] = np.degrees(df['theta_rad'])
    
    # Components of the phase angle (direction of the amplification vector)
    df['cos_theta'] = np.cos(df['theta_rad']) # Real alignment (how much stays on the real axis)
    df['sin_theta'] = np.sin(df['theta_rad']) # Imaginary alignment (how much rotates into the orthogonal plane)
    
    # Sort by Coherence (Cf) to observe the phase shift as coherence increases
    df = df.sort_values('cf', ascending=False)
    
    print("="*95)
    print("      EULER PHASE DIAGNOSTIC: REAL vs. MAGNITUDE TRADE-OFF")
    print("="*95)
    print(f"{'Pixel':<8} | {'Cf':>6} | {'M':>6} | {'A_lin':>7} | {'A_quad':>7} | {'θ (deg)':>8} | {'cos(θ)':>7} | {'sin(θ)':>7}")
    print("-" * 95)
    
    # Display the top 15 highest coherence pixels
    for idx, row in df.head(15).iterrows():
        print(f"{int(row['pixel_id']):<8} | {row['cf']:>6.3f} | {row['M']:>6.3f} | {row['A_linear']:>7.3f} | {row['A_quad']:>7.3f} | {row['theta_deg']:>8.2f} | {row['cos_theta']:>7.3f} | {row['sin_theta']:>7.3f}")
        
    # 4. Correlation: Does phase angle track with coherence?
    corr_cf_theta = df['cf'].corr(df['theta_deg'])
    
    print("\n" + "="*95)
    print("      PHASE SHIFT CORRELATION")
    print("="*95)
    print(f"Correlation (Cf vs θ): {corr_cf_theta:.4f}")
    
    if corr_cf_theta > 0.7:
        print("✅ STRONG PHASE SHIFT: As kinematic coherence increases, the amplification")
        print("   vector rotates significantly into the imaginary (orthogonal) plane.")
        print("   The linear model (real part only) systematically ignores this growing rotation.")
    else:
        print("⚠️ WEAK PHASE SHIFT: The rotation remains relatively constant or small")
        print("   across the coherence spectrum.")
        
    # Save
    out_file = 'data/sandbox_euler_phase_enriched.csv'
    df.to_csv(out_file, index=False)
    print(f"\n💾 Saved Euler phase matrix to: {out_file}")
    print("="*95)

if __name__ == "__main__":
    run_euler_phase_analysis()