import pandas as pd
import numpy as np
import os
import time
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.mast import Catalogs
from scipy.stats import fisher_exact

def run_tess_variability_test_v2():
    # Dynamically find project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    target_file = os.path.join(project_root, 'data', 'phase12a_target_galex_v2.csv')
    control_file = os.path.join(project_root, 'data', 'phase12a_control_galex_v2.csv')
    
    if not os.path.exists(target_file) or not os.path.exists(control_file):
        print("❌ Missing Phase 12A crossmatch files. Run phase12a first.")
        return

    print("📥 Loading Phase 12A Matched Pairs...")
    targets = pd.read_csv(target_file)
    controls = pd.read_csv(control_file)
    print(f"🎯 Loaded {len(targets)} matched pairs for TIC Variability Test (V2).\n")

    # =========================================================================
    # 1. QUERY TESS INPUT CATALOG (TIC) - STRICT 3 ARCSEC RADIUS
    # =========================================================================
    print("📡 Querying MAST TESS Input Catalog (TIC) within 3 arcseconds...")
    
    def get_tic_data(ra, dec):
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        try:
            # MORPHEUS FIX: Strict 3 arcsecond radius to prevent false matches
            result = Catalogs.query_region(coord, radius=3*u.arcsec, catalog="TIC")
            if result and len(result) > 0:
                # Grab the closest match (first row)
                tic_id = str(result['ID'][0])
                tmag = float(result['Tmag'][0]) if 'Tmag' in result.colnames and result['Tmag'][0] is not None else np.nan
                
                # Check for variability flag
                varflag = "None"
                if 'varflag' in result.colnames and result['varflag'][0] is not None:
                    varflag = str(result['varflag'][0])
                    
                return tic_id, tmag, varflag
        except Exception:
            pass
        return "No_Match", np.nan, "No_Match"

    target_data = []
    control_data = []
    
    for i in range(len(targets)):
        t_id, t_tmag, t_var = get_tic_data(targets.iloc[i]['ra'], targets.iloc[i]['dec'])
        c_id, c_tmag, c_var = get_tic_data(controls.iloc[i]['ra'], controls.iloc[i]['dec'])
        
        target_data.append({'tic_id': t_id, 'tmag': t_tmag, 'varflag': t_var})
        control_data.append({'tic_id': c_id, 'tmag': c_tmag, 'varflag': c_var})
        
        print(f"   [{i+1}/{len(targets)}] Target TIC: {t_var:<10} | Control TIC: {c_var}")
        time.sleep(0.3) # Respect MAST rate limits
        
    t_tic_df = pd.DataFrame(target_data)
    c_tic_df = pd.DataFrame(control_data)
    
    targets = pd.concat([targets.reset_index(drop=True), t_tic_df], axis=1)
    controls = pd.concat([controls.reset_index(drop=True), c_tic_df], axis=1)

    # =========================================================================
    # 2. STATISTICAL ANALYSIS (Cataloged Variability Enrichment)
    # =========================================================================
    print("\n" + "="*85)
    print("PHASE 12 PRIORITY 1 VERDICT: CATALOGED OPTICAL VARIABILITY")
    print("="*85)
    
    # A star is "cataloged variable" if varflag is not 'None' and not 'No_Match'
    def is_cataloged_var(flag):
        return flag not in ['None', 'No_Match', 'nan', None]

    t_var_count = sum([is_cataloged_var(f) for f in targets['varflag']])
    c_var_count = sum([is_cataloged_var(f) for f in controls['varflag']])
    
    t_nondet = len(targets) - t_var_count
    c_nondet = len(controls) - c_var_count
    
    print("TEST: TIC CATALOGED VARIABLE FRACTION")
    print(f"Targets flagged in TIC:  {t_var_count}/{len(targets)} ({t_var_count/len(targets)*100:.1f}%)")
    print(f"Controls flagged in TIC: {c_var_count}/{len(controls)} ({c_var_count/len(controls)*100:.1f}%)")
    
    table = [[t_var_count, t_nondet], [c_var_count, c_nondet]]
    _, p_var = fisher_exact(table, alternative='greater')
    print(f"Fisher Exact p-value (Targets > Controls): {p_var:.4e}\n")
    
    # =========================================================================
    # 3. MORPHEUS SYNTHESIS (Epistemologically Disciplined)
    # =========================================================================
    print("="*85)
    print("TRACEBIND PHASE 12: EVIDENCE HIERARCHY UPDATE")
    print("="*85)
    
    if p_var < 0.05:
        print("⚠️ ENRICHMENT IN CATALOGED VARIABLES DETECTED.")
        print("   The targets are significantly more likely to be known optical variables.")
        print("   The 'Active Spotted Dwarf' hypothesis remains viable.")
    else:
        print("❌ NO EVIDENCE OF ENRICHMENT IN CATALOGED VARIABLES.")
        print("   We find no evidence that the TRACEBIND population is enriched in")
        print("   cataloged TIC variables relative to matched controls.")
        print("")
        print("   IMPORTANT: This does NOT prove the stars are photometrically quiet.")
        print("   It only proves they are not currently flagged in the TIC.")
        print("")
        print("   COMBINED WITH GALEX (UV Null) + TIC (Optical Null):")
        print("   The 'Stellar Activity' hypothesis is weakening. The balance of evidence")
        print("   now shifts heavily toward UNRESOLVED MULTIPLICITY (Hidden Companions).")
        print("")
        print("   NEXT ACTION REQUIRED: Phase 12 Priority 2 (Multiplicity Crossmatch).")
        print("   We must test if these stars are already known binaries in WDS/SB9.")
        
    print("="*85)
    
    # Save results
    out_dir = os.path.join(project_root, 'data')
    targets.to_csv(os.path.join(out_dir, 'phase12_priority1_target_tic_v2.csv'), index=False)
    controls.to_csv(os.path.join(out_dir, 'phase12_priority1_control_tic_v2.csv'), index=False)
    print("💾 Saved V2 TIC crossmatch results to data/")

if __name__ == "__main__":
    run_tess_variability_test_v2()