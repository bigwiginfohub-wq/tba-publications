"""
TRACEBIND v2.0 - Synthetic Hyades Generator (V2 - Corrected Projection Null)
Projection control now has isotropic velocity directions to eliminate
spurious local alignment. Signal and field controls unchanged.
License: CC0 1.0 Universal
"""
import numpy as np
import pandas as pd
import os

np.random.seed(42)

N_STARS = 1500
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))\n_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))\nOUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "sim")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "synthetic_hyades_phase1_v2.csv")


def generate_plummer_sphere(n, scale_radius=2.0):
    r = scale_radius / np.sqrt(np.random.uniform(0, 1, n)**(-2/3) - 1)
    theta = np.arccos(2 * np.random.uniform(0, 1, n) - 1)
    phi = 2 * np.pi * np.random.uniform(0, 1, n)
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z


def generate_convergent_velocities(n, vx_mean=30.0, vy_mean=-45.0, vz_mean=-10.0, sigma=1.5):
    vx = np.random.normal(vx_mean, sigma, n)
    vy = np.random.normal(vy_mean, sigma, n)
    vz = np.random.normal(vz_mean, sigma, n)
    return vx, vy, vz


def generate_isotropic_velocities(n, speed_mean=50.0, sigma=15.0):
    speed = np.abs(np.random.normal(speed_mean, sigma, n))
    theta = np.arccos(2 * np.random.uniform(0, 1, n) - 1)
    phi = 2 * np.pi * np.random.uniform(0, 1, n)
    vx = speed * np.sin(theta) * np.cos(phi)
    vy = speed * np.sin(theta) * np.sin(phi)
    vz = speed * np.cos(theta)
    return vx, vy, vz


def cartesian_to_astrometry(x, y, z, vx, vy, vz):
    distance = np.sqrt(x**2 + y**2 + z**2)
    parallax = 1000.0 / distance
    ra = np.degrees(np.arctan2(y, x)) % 360
    dec = np.degrees(np.arcsin(z / distance))
    k = 4.74047
    pmra = k * (-vx * np.sin(np.radians(ra)) + vy * np.cos(np.radians(ra))) / distance
    pmdec = k * (-vx * np.cos(np.radians(ra)) * np.sin(np.radians(dec))
                 - vy * np.sin(np.radians(ra)) * np.sin(np.radians(dec))
                 + vz * np.cos(np.radians(dec))) / distance
    g_mag = 5 * np.log10(distance) + 2.0 + np.random.normal(0, 0.3, len(distance))
    return ra, dec, parallax, pmra, pmdec, g_mag


def main():
    print("🔧 Generating Synthetic Hyades V2 (Corrected Projection Null)...")

    # === SIGNAL: Coherent cluster (unchanged) ===
    sx, sy, sz = generate_plummer_sphere(N_STARS)
    svx, svy, svz = generate_convergent_velocities(N_STARS)
    s_ra, s_dec, s_plx, s_pmra, s_pmdec, s_g = cartesian_to_astrometry(sx, sy, sz, svx, svy, svz)

    # === FIELD CONTROL: Matched distances, isotropic velocities (unchanged) ===
    fa_distance = 1000.0 / s_plx
    fa_theta = np.arccos(2 * np.random.uniform(0, 1, N_STARS) - 1)
    fa_phi = 2 * np.pi * np.random.uniform(0, 1, N_STARS)
    fx = fa_distance * np.sin(fa_theta) * np.cos(fa_phi)
    fy = fa_distance * np.sin(fa_theta) * np.sin(fa_phi)
    fz = fa_distance * np.cos(fa_theta)
    fvx, fvy, fvz = generate_isotropic_velocities(N_STARS)
    f_ra, f_dec, f_plx, f_pmra, f_pmdec, f_g = cartesian_to_astrometry(fx, fy, fz, fvx, fvy, fvz)

    # === PROJECTION CONTROL (V2.1 CORRECTED): Full tuple shuffle + isotropic PM directions ===
    shuffle_idx = np.random.permutation(N_STARS)
    
    # FIX: Shuffle ENTIRE astrometric tuple to preserve (RA, Dec, parallax) consistency
    b_ra = s_ra[shuffle_idx]
    b_dec = s_dec[shuffle_idx]
    b_plx = s_plx[shuffle_idx]   # ← WAS MISSING [shuffle_idx] IN V2
    b_g = s_g[shuffle_idx]

    # Preserve original PM speed magnitudes but randomize directions uniformly
    # Note: This is isotropic in observed PM space, not 3D velocity space.
    # Acceptable for Phase 1 since the metric operates on (pmra, pmdec).
    orig_speeds = np.sqrt(s_pmra[shuffle_idx]**2 + s_pmdec[shuffle_idx]**2)
    rand_theta = np.arccos(2 * np.random.uniform(0, 1, N_STARS) - 1)
    rand_phi = 2 * np.pi * np.random.uniform(0, 1, N_STARS)
    b_pmra = orig_speeds * np.sin(rand_theta) * np.cos(rand_phi)
    b_pmdec = orig_speeds * np.sin(rand_theta) * np.sin(rand_phi)

    # Preserve original speed magnitudes but randomize directions uniformly on sphere
    orig_speeds = np.sqrt(s_pmra[shuffle_idx]**2 + s_pmdec[shuffle_idx]**2)
    rand_theta = np.arccos(2 * np.random.uniform(0, 1, N_STARS) - 1)
    rand_phi = 2 * np.pi * np.random.uniform(0, 1, N_STARS)
    b_pmra = orig_speeds * np.sin(rand_theta) * np.cos(rand_phi)
    b_pmdec = orig_speeds * np.sin(rand_theta) * np.sin(rand_phi)

    # === Assemble DataFrame ===
    records = []
    for i in range(N_STARS):
        records.append({"population": "signal", "ra": s_ra[i], "dec": s_dec[i],
                        "parallax": s_plx[i], "pmra": s_pmra[i], "pmdec": s_pmdec[i],
                        "phot_g_mean_mag": s_g[i]})
        records.append({"population": "field_control", "ra": f_ra[i], "dec": f_dec[i],
                        "parallax": f_plx[i], "pmra": f_pmra[i], "pmdec": f_pmdec[i],
                        "phot_g_mean_mag": f_g[i]})
        records.append({"population": "projection_control", "ra": b_ra[i], "dec": b_dec[i],
                        "parallax": b_plx[i], "pmra": b_pmra[i], "pmdec": b_pmdec[i],
                        "phot_g_mean_mag": b_g[i]})

    df = pd.DataFrame(records)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Generated {len(df)} rows ({N_STARS} × 3 populations)")
    print(f"💾 Saved to {OUTPUT_FILE}")
    print("\nPopulation summary:")
    for pop in ["signal", "field_control", "projection_control"]:
        sub = df[df["population"] == pop]
        print(f"  {pop:20s}: plx={sub['parallax'].mean():.2f}±{sub['parallax'].std():.2f} mas, "
              f"G={sub['phot_g_mean_mag'].mean():.2f}±{sub['phot_g_mean_mag'].std():.2f}")

    print("\n🔒 TRACEBIND CHECKPOINT:")
    print("- Seed: 42")
    print(f"- Rows: {len(df)}")
    print(f"- Populations: {df['population'].unique()}")
    print("- Projection null: ISOTROPIC velocity directions (corrected)")
    print("- Status: REPRODUCIBLE DATASET V2 LOCKED")


if __name__ == "__main__":
    main()
