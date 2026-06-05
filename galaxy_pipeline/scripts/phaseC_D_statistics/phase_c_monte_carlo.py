import pandas as pd
import numpy as np
import os
from astropy.coordinates import SkyCoord
import astropy.units as u

def run_monte_carlo_validation():
    input_file = 'data/phase_c_crossmatch_targets.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} patches for Monte Carlo Significance Testing.\n")

    # Crude Catalog (Acknowledging Morpheus's caveat: these are circular approximations)
    KNOWN_STRUCTURES = [
        {"name": "Hyades Moving Group", "ra": 67.5, "dec": 15.5, "radius": 15.0},
        {"name": "Pleiades Moving Group", "ra": 56.5, "dec": 24.0, "radius": 15.0},
        {"name": "Coma Berenices Cluster", "ra": 185.0, "dec": 26.0, "radius": 15.0},
        {"name": "Ursa Major Moving Group", "ra": 180.0, "dec": 55.0, "radius": 15.0},
        {"name": "Sagittarius Stream (North)", "ra": 45.0, "dec": 60.0, "radius": 25.0},
        {"name": "Sagittarius Stream (South)", "ra": 270.0, "dec": -30.0, "radius": 25.0},
        {"name": "GD-1 Stream", "ra": 160.0, "dec": 45.0, "radius": 20.0},
        {"name": "Orphan Stream", "ra": 230.0, "dec": 5.0, "radius": 20.0},
        {"name": "Palomar 5 Stream", "ra": 225.0, "dec": -10.0, "radius": 15.0},
        {"name": "Helmi Streams", "ra": 210.0, "dec": -40.0, "radius": 20.0}
    ]

    def count_overlaps(patch_subset):
        matches = 0
        for _, row in patch_subset.iterrows():
            patch_coord = SkyCoord(ra=row['center_ra']*u.deg, dec=row['center_dec']*u.deg, frame='icrs')
            hit = False
            for struct in KNOWN_STRUCTURES:
                struct_coord = SkyCoord(ra=struct['ra']*u.deg, dec=struct['dec']*u.deg, frame='icrs')
                if patch_coord.separation(struct_coord).deg <= struct['radius']:
                    hit = True
                    break
            if hit:
                matches += 1
        return matches

    TOP_N = 10
    observed_patches = df.sort_values('cf', ascending=False).head(TOP_N)
    observed_matches = count_overlaps(observed_patches)
    
    print("="*85)
    print("PART 1: OBSERVED OVERLAPS (Top High-Cf Patches)")
    print("="*85)
    print(f"Out of the top {TOP_N} highest-coherence patches, {observed_matches} overlap with known structures.\n")
    
    for _, row in observed_patches.iterrows():
        patch_coord = SkyCoord(ra=row['center_ra']*u.deg, dec=row['center_dec']*u.deg, frame='icrs')
        hit_name = "None"
        for struct in KNOWN_STRUCTURES:
            struct_coord = SkyCoord(ra=struct['ra']*u.deg, dec=struct['dec']*u.deg, frame='icrs')
            if patch_coord.separation(struct_coord).deg <= struct['radius']:
                hit_name = struct['name']
                break
        print(f"  Patch {row['ra_bin']}-{row['dec_bin']} (Cf={row['cf']:.3f}) -> {hit_name}")

    print("\n" + "="*85)
    print("PART 2: MONTE CARLO NULL MODEL (The Baseline of Ignorance)")
    print("="*85)
    print(f"Running 1,000 random selections of {TOP_N} patches to establish chance probability...")
    
    np.random.seed(42)
    N_ITERATIONS = 1000
    random_matches = []
    
    for _ in range(N_ITERATIONS):
        random_subset = df.sample(n=TOP_N)
        random_matches.append(count_overlaps(random_subset))
        
    random_matches = np.array(random_matches)
    p_value = np.sum(random_matches >= observed_matches) / N_ITERATIONS
    mean_random = np.mean(random_matches)
    
    print(f"\nNull Model Results:")
    print(f"  Average random overlaps: {mean_random:.2f} patches")
    print(f"  Observed overlaps:       {observed_matches} patches")
    print(f"  p-value:                 {p_value:.4f}")
    
    print("\n" + "="*85)
    print("FINAL ASTROPHYSICAL VERDICT")
    print("="*85)
    if p_value < 0.01:
        print("✅ STRONG STATISTICAL EVIDENCE (p < 0.01)")
        print("   High-Cf patches preferentially identify known coherent stellar structures")
        print("   significantly more often than random chance.")
    elif p_value < 0.05:
        print("⚠️ MODERATE EVIDENCE (p < 0.05)")
        print("   There is a statistically significant trend, but it is not overwhelming.")
    else:
        print("❌ NO STATISTICAL SIGNIFICANCE (p >= 0.05)")
        print("   The observed overlaps are consistent with random chance.")
        print("   High-Cf patches do not preferentially target these specific catalogued structures.")
        
    print("\nMorpheus's Epistemological Boundary:")
    print("1. Mathematical Validity: SETTLED. Cf is the Mean Resultant Length.")
    print("2. Astrophysical Interpretation: This test uses crude circular approximations.")
    print("   A positive p-value suggests Cf highlights kinematic substructure, but does not")
    print("   prove the stars *belong* to the stream without 3D phase-space confirmation.")
    print("="*85)

if __name__ == "__main__":
    run_monte_carlo_validation()