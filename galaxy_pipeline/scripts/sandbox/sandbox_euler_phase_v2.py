import pandas as pd
import numpy as np
import os

def run_euler_phase_analysis_v2(alpha=0.1, beta=0.1, gamma=0.05):
    input_file = 'data/phase9_allsky_coherence_map.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} sky pixels for Euler Phase Analysis v2.\n")

    # 1. Reconstruct normalized variables and Modification term (M)
    df['rho_norm'] = df['star_count'] / df['star_count'].max()
    df['interaction'] = df['rho_norm'] * df['cf']
    
    df['M'] = (alpha * df['rho_norm']) + (beta * df['cf']) + (gamma * df['interaction'])
    
    # 2. Amplification Models
    df['A_linear'] = 1 + df['M']
    df['A_quad'] = np.sqrt(1 + df['M']**2) 
    
    # 3. Euler's Formula / Complex Plane Diagnostics
    df['theta_rad'] = np.arctan(df['M'])
    df['theta_deg'] = np.degrees(df['theta_rad'])
    
    # Sort by M (Modification magnitude) to see the biggest rotations
    df = df.sort_values('M', ascending=False)
    
    print("="*85)
    print("      EULER PHASE DIAGNOSTIC v2: FEATURE ATTRIBUTION")
    print("="*85)
    print(f"{'Pixel':<8} | {'Cf':>6} | {'ρ (norm)':>8} | {'ρ×Cf':>6} | {'M':>6} | {'θ (deg)':>8}")
    print("-" * 85)
    
    for idx, row in df.head(10).iterrows():
        print(f"{int(row['pixel_id']):<8} | {row['cf']:>6.3f} | {row['rho_norm']:>8.3f} | {row['interaction']:>6.3f} | {row['M']:>6.3f} | {row['theta_deg']:>8.2f}")
        
    # 4. Correlation Matrix (The Reviewer's Hypothesis Test)
    corr_cf_theta = df['cf'].corr(df['theta_deg'])
    corr_rho_theta = df['rho_norm'].corr(df['theta_deg'])
    corr_int_theta = df['interaction'].corr(df['theta_deg'])
    
    print("\n" + "="*85)
    print("      FEATURE DRIVER CORRELATIONS (vs Phase Angle θ)")
    print("="*85)
    print(f"1. Coherence (Cf) vs θ       : r = {corr_cf_theta:.4f}")
    print(f"2. Density (ρ) vs θ          : r = {corr_rho_theta:.4f}")
    print(f"3. Interaction (ρ × Cf) vs θ : r = {corr_int_theta:.4f}")
    
    print("\n" + "="*85)
    print("      DIAGNOSTIC VERDICT")
    print("="*85)
    
    if corr_int_theta > corr_cf_theta and corr_int_theta > corr_rho_theta:
        print("✅ INTERACTION DOMINANCE CONFIRMED.")
        print("   The phase rotation (θ) is primarily driven by regions where BOTH")
        print("   high density and high coherence occur simultaneously (ρ × Cf).")
        print("   Coherence alone is not the sole driver of the amplification vector.")
    elif corr_rho_theta > corr_cf_theta:
        print("✅ DENSITY DOMINANCE.")
        print("   The phase rotation is primarily driven by stellar density (ρ).")
    else:
        print("⚠️ COHERENCE DOMINANCE.")
        print("   The phase rotation is primarily driven by kinematic coherence (Cf).")

    out_file = 'data/sandbox_euler_phase_v2_enriched.csv'
    df.to_csv(out_file, index=False)
    print(f"\n💾 Saved Euler phase matrix to: {out_file}")
    print("="*85)

if __name__ == "__main__":
    run_euler_phase_analysis_v2()