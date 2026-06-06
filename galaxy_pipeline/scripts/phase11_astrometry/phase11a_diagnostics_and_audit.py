import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import time
from astroquery.simbad import Simbad
import astropy.units as u
from astropy.coordinates import SkyCoord

def run_diagnostics_and_audit():
    input_file = 'data/phase11a_local_tension_features.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}. Run Stage A first.")
        return

    df = pd.read_csv(input_file)
    df['distance_pc'] = 1000.0 / df['parallax']
    
    print(f"📋 Loaded {len(df)} targets for Phase 11A Diagnostics.\n")

    # =========================================================================
    # PART 1: MORPHEUS DIAGNOSTIC PLOTS
    # =========================================================================
    print("📊 Generating diagnostic distributions...")
    os.makedirs('figures', exist_ok=True)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('TRACEBIND Phase 11A: Astrometric Tension Diagnostics', fontsize=16, fontweight='bold')

    # 1. RUWE Distribution
    axes[0, 0].hist(df['ruwe'].clip(upper=10), bins=100, color='teal', edgecolor='black')
    axes[0, 0].set_title('RUWE Distribution (Clipped at 10)')
    axes[0, 0].axvline(1.4, color='red', linestyle='--', label='RUWE = 1.4')
    axes[0, 0].set_xlabel('RUWE')
    axes[0, 0].set_ylabel('Count')
    axes[0, 0].legend()

    # 2. Excess Noise Distribution
    axes[0, 1].hist(df['astrometric_excess_noise'].clip(upper=5), bins=100, color='purple', edgecolor='black')
    axes[0, 1].set_title('Astrometric Excess Noise (mas)')
    axes[0, 1].set_xlabel('Excess Noise (mas)')
    axes[0, 1].set_ylabel('Count')

    # 3. Tension Score Distribution
    axes[0, 2].hist(df['tension_score'], bins=100, color='darkorange', edgecolor='black')
    axes[0, 2].set_title('Composite Tension Score')
    axes[0, 2].axvline(0.5, color='red', linestyle='--', label='Threshold = 0.5')
    axes[0, 2].set_xlabel('Tension Score')
    axes[0, 2].set_ylabel('Count')
    axes[0, 2].legend()

    # 4. Distance vs Tension Score (Selection Effects Check)
    axes[1, 0].scatter(df['distance_pc'], df['tension_score'], alpha=0.1, s=10, color='gray')
    axes[1, 0].set_title('Distance vs. Tension Score')
    axes[1, 0].set_xlabel('Distance (pc)')
    axes[1, 0].set_ylabel('Tension Score')
    axes[1, 0].set_xlim(0, 55)

    # 5. Tangential Velocity vs Tension Score
    axes[1, 1].scatter(df['vt_kms'], df['tension_score'], alpha=0.1, s=10, color='blue')
    axes[1, 1].set_title('Tangential Velocity vs. Tension Score')
    axes[1, 1].set_xlabel('Vt (km/s)')
    axes[1, 1].set_ylabel('Tension Score')
    axes[1, 1].set_xlim(0, 200) # Clip for visibility

    # Hide the empty 6th subplot
    axes[1, 2].axis('off')

    plt.tight_layout()
    plt.savefig('figures/phase11a_diagnostics.png', dpi=300)
    print("✅ Saved diagnostic plots to figures/phase11a_diagnostics.png\n")

    # =========================================================================
    # PART 2: TOP 50 EXTREME TENSION EXPORT
    # =========================================================================
    top50 = df.sort_values('tension_score', ascending=False).head(50)
    top50_file = 'data/phase11a_top50_tension_targets.csv'
    top50.to_csv(top50_file, index=False)
    print(f"💾 Exported Top 50 extreme tension targets to {top50_file}\n")

    # =========================================================================
    # PART 3: THE CRITICAL QUESTION (SIMBAD BINARY AUDIT)
    # =========================================================================
    print("="*85)
    print("PART 3: SIMBAD BINARY AUDIT (Answering Morpheus's Critical Question)")
    print("="*85)
    print("Querying SIMBAD for the Top 50 highest-tension stars to check for known binaries...")
    
    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('otype', 'main_id')
    
    # SIMBAD object types that indicate multiple star systems / binaries
    binary_flags = {'**', 'SB*', 'EB*', 'Al*', 'WU*', 'RS*', 'SB?', 'El*', 'PM'}
    
    audit_results = []
    binary_count = 0
    
    for idx, row in top50.iterrows():
        coord = SkyCoord(ra=row['ra']*u.deg, dec=row['dec']*u.deg, frame='icrs')
        
        otype = "No Match"
        main_id = "Unknown"
        is_binary = False
        
        try:
            # Query a 2 arcsecond radius around the target
            result = custom_simbad.query_region(coord, radius=2*u.arcsec)
            
            if result is not None and len(result) > 0:
                # Extract the first (closest) match
                main_id = str(result['main_id'][0]).strip()
                otype_raw = str(result['otype'][0]).strip()
                otype = otype_raw
                
                # Check if it's a known binary
                if otype in binary_flags:
                    is_binary = True
                    binary_count += 1
                    
        except Exception as e:
            otype = f"Query Error"
            
        audit_results.append({
            'source_id': row['source_id'],
            'tension_score': row['tension_score'],
            'ruwe': row['ruwe'],
            'distance_pc': row['distance_pc'],
            'simbad_main_id': main_id,
            'simbad_otype': otype,
            'is_known_binary': is_binary
        })
        
        # Print progress and be nice to the SIMBAD server
        status = "🔴 BINARY" if is_binary else "🟢 SINGLE/OTHER"
        print(f"  [{len(audit_results)}/50] {main_id:<20} | Otype: {otype:<5} | {status}")
        time.sleep(0.8) 

    # Save Audit Results
    audit_df = pd.DataFrame(audit_results)
    audit_df.to_csv('data/phase11a_top50_simbad_audit.csv', index=False)
    
    # Final Verdict
    pct_binary = (binary_count / 50) * 100
    print("\n" + "="*85)
    print("MORPHEUS'S CRITICAL QUESTION: ANSWERED")
    print("="*85)
    print(f"Out of the Top 50 highest-tension stars, {binary_count} ({pct_binary:.1f}%) are known binaries.")
    
    if pct_binary >= 70:
        print("✅ VERDICT: TRACEBIND is correctly detecting known astrometric model failures.")
        print("   The tension score is a highly reliable proxy for unresolved stellar multiplicity.")
    elif pct_binary >= 30:
        print("⚠️ VERDICT: MIXED POPULATION.")
        print("   TRACEBIND is finding known binaries, but also flagging other anomalies")
        print("   (e.g., calibration issues, crowded fields, or undiscovered companions).")
    else:
        print("❌ VERDICT: UNEXPECTED RESULTS.")
        print("   The highest tension scores are NOT dominated by known binaries.")
        print("   This implies either a poorly calibrated metric, or the discovery of")
        print("   a population of anomalies missed by current catalogs.")
    print("="*85)

if __name__ == "__main__":
    run_diagnostics_and_audit()