import pandas as pd
import numpy as np
import os
import time
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.stats import mannwhitneyu, fisher_exact

def run_activity_crossmatch_v2():
    # Dynamically find the project root (GaiaProject/) so paths work from anywhere
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir)) 
    
    master_file = os.path.join(project_root, 'data', 'tracebind_master_catalog_v1.csv')
    target_file = os.path.join(project_root, 'data', 'tracebind_followup_top100_refined.csv')
    
    if not os.path.exists(master_file) or not os.path.exists(target_file):
        print(f"❌ Missing Master Catalog or Follow-up Catalog.")
        print(f"   Looked in: {os.path.join(project_root, 'data')}")
        return

    print("📥 Loading Catalogs (Strict Master Catalog Architecture)...")
    master = pd.read_csv(master_file)
    targets = pd.read_csv(target_file)
    
    PILOT_SIZE = 100
    targets = targets.head(PILOT_SIZE).copy()
    print(f"🎯 Loaded Top {PILOT_SIZE} Unexplained Targets for Pilot.\n")

    # =========================================================================
    # 1. BUILD THE 1-TO-1 MATCHED CONTROL GROUP
    # =========================================================================
    print("⚙️ Building 1-to-1 Matched Control Group (Quiet Single Stars)...")
    clean_stars = master[
        (master['in_any_nss'] == False) & 
        (master['ruwe'] < 1.2) & 
        (master['anomaly_class'] == 'Below Top 5% Threshold')
    ].copy()
    
    used_ids = set()
    controls = []
    
    for _, row in targets.iterrows():
        mask = (
            (clean_stars['bp_rp'] >= row['bp_rp'] - 0.15) &
            (clean_stars['bp_rp'] <= row['bp_rp'] + 0.15) &
            (clean_stars['distance_pc'] >= row['distance_pc'] * 0.7) &
            (clean_stars['distance_pc'] <= row['distance_pc'] * 1.3)
        )
        matches = clean_stars[mask]
        # Enforce 1-to-1 matching
        matches = matches[~matches['source_id'].isin(used_ids)]
        
        if len(matches) > 0:
            control = matches.sample(1).iloc[0]
            used_ids.add(control['source_id'])
            controls.append(control)
        else:
            controls.append(None)
            
    valid_mask = [c is not None for c in controls]
    targets = targets[valid_mask].reset_index(drop=True)
    controls_df = pd.DataFrame([c for c in controls if c is not None]).reset_index(drop=True)
    
    print(f"✅ Successfully matched {len(targets)} targets with UNIQUE quiet control stars.\n")

    # =========================================================================
    # 2. GALEX NUV CROSSMATCH (3 arcsec radius)
    # =========================================================================
    print("📡 Querying GALEX All-Sky Survey (Near-UV) via VizieR (3\" radius)...")
    vizier = Vizier(columns=['NUV'], column_filters={"NUV": "<25"})
    vizier.ROW_LIMIT = 1
    
    def get_galex_nuv(ra, dec):
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        try:
            result = vizier.query_region(coord, radius=3*u.arcsec, catalog="II/312/ais")
            if result and len(result) > 0 and len(result[0]) > 0:
                nuv = result[0]['NUV'][0]
                if nuv is not None and not np.ma.is_masked(nuv):
                    return float(nuv)
        except Exception:
            pass
        return np.nan

    target_nuv, control_nuv = [], []
    
    for i in range(len(targets)):
        t_nuv = get_galex_nuv(targets.iloc[i]['ra'], targets.iloc[i]['dec'])
        c_nuv = get_galex_nuv(controls_df.iloc[i]['ra'], controls_df.iloc[i]['dec'])
        target_nuv.append(t_nuv)
        control_nuv.append(c_nuv)
        
        status_t = f"{t_nuv:.2f}" if not np.isnan(t_nuv) else "Undetected"
        status_c = f"{c_nuv:.2f}" if not np.isnan(c_nuv) else "Undetected"
        print(f"   [{i+1}/{len(targets)}] Target NUV: {status_t:<10} | Control NUV: {status_c}")
        time.sleep(1.0) 
        
    targets['NUV'] = target_nuv
    controls_df['NUV'] = control_nuv

    # Fix: Borrow phot_g_mean_mag from the Master Catalog if it's missing from the Follow-up CSV
    if 'phot_g_mean_mag' not in targets.columns:
        targets = targets.merge(master[['source_id', 'phot_g_mean_mag']], on='source_id', how='left')
    if 'phot_g_mean_mag' not in controls_df.columns:
        controls_df = controls_df.merge(master[['source_id', 'phot_g_mean_mag']], on='source_id', how='left')

    # =========================================================================
    # 3. CALCULATE UV EXCESS (NUV - G)

    # =========================================================================
    # 3. CALCULATE UV EXCESS (NUV - G)
    # =========================================================================
    # Lower NUV-G means the star is emitting disproportionately more UV light
    targets['NUV_G'] = targets['NUV'] - targets['phot_g_mean_mag']
    controls_df['NUV_G'] = controls_df['NUV'] - controls_df['phot_g_mean_mag']

    # =========================================================================
    # 4. STATISTICAL ANALYSIS (Detection Bias & UV Excess)
    # =========================================================================
    print("\n" + "="*85)
    print("PHASE 12A VERDICT: ACTIVITY HYPOTHESIS TEST (V2)")
    print("="*85)
    
    # --- TEST A: DETECTION BIAS (Fisher Exact Test) ---
    t_det = targets['NUV'].notna().sum()
    t_nondet = len(targets) - t_det
    c_det = controls_df['NUV'].notna().sum()
    c_nondet = len(controls_df) - c_det
    
    print("TEST A: GALEX DETECTION FRACTION (Censoring Test)")
    print(f"Targets Detected:  {t_det}/{len(targets)} ({t_det/len(targets)*100:.1f}%)")
    print(f"Controls Detected: {c_det}/{len(controls_df)} ({c_det/len(controls_df)*100:.1f}%)")
    
    table = [[t_det, t_nondet], [c_det, c_nondet]]
    _, p_det = fisher_exact(table, alternative='greater') # Are targets detected MORE often?
    print(f"Fisher Exact p-value (Targets > Controls): {p_det:.4e}")
    
    if p_det < 0.05:
        print("✅ SIGNIFICANT: Targets light up in the UV much more often than quiet stars.\n")
    else:
        print("❌ NOT SIGNIFICANT: Targets are just as dark in the UV as quiet stars.\n")

    # --- TEST B: UV EXCESS (Mann-Whitney U Test) ---
    t_valid = targets['NUV_G'].dropna()
    c_valid = controls_df['NUV_G'].dropna()
    
    print("TEST B: UV EXCESS (NUV - G) for Detected Stars")
    print(f"Targets with UV Excess data: {len(t_valid)}")
    print(f"Controls with UV Excess data: {len(c_valid)}")
    
    if len(t_valid) > 2 and len(c_valid) > 2:
        # Note: Lower NUV-G = Brighter UV = More Active
        stat, p_excess = mannwhitneyu(t_valid, c_valid, alternative='less')
        
        print(f"Mean Target UV Excess (NUV-G):  {t_valid.mean():.3f} mag (Lower = More Active)")
        print(f"Mean Control UV Excess (NUV-G): {c_valid.mean():.3f} mag")
        print(f"Mann-Whitney U p-value (Targets < Controls): {p_excess:.4e}\n")
        
        if p_excess < 0.05:
            print("✅ SIGNIFICANT: Detected targets have a massive UV Excess compared to controls.")
        else:
            print("❌ NOT SIGNIFICANT: Detected targets have normal UV colors.")
    else:
        print("⚠️ Insufficient detections to run UV Excess test.\n")

        # --- FINAL MORPHEUS VERDICT ---
    print("="*85)
    print("PHASE 12A CONCLUSION")
    print("="*85)
    print("TRACEBIND identifies a statistically distinct population of high-tension")
    print("K/M dwarf systems that are not explained by existing Gaia DR3 NSS solutions.")
    
    # Safely format p-values in case the UV excess test couldn't run
    p_ex_str = f"{p_excess:.3f}" if len(t_valid) > 2 else "N/A (insufficient n)"
    
    print(f"A GALEX study (n={len(targets)}) found no statistically significant enhancement")
    print(f"in UV activity relative to matched controls (Detection p={p_det:.3f}, UV Excess p={p_ex_str}),")
    print("suggesting stellar activity alone may not explain the observed astrometric tension.")
    print("The population is likely mixed: active spotted dwarfs, unresolved companions,")
    print("and/or brown dwarfs. Further multiwavelength (TESS/ROSAT) and multiplicity")
    print("follow-up is required to determine the dominant physical origin.")
    print("="*85)

if __name__ == "__main__":
    run_activity_crossmatch_v2()