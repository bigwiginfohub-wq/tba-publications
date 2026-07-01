import pandas as pd
import numpy as np
import os
import time
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier
from scipy.stats import fisher_exact

def get_status(w, s):
    if w and s: return "WDS+SB9"
    if w: return "WDS"
    if s: return "SB9"
    return "None"

def run_multiplicity_crossmatch_v2():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    target_file = os.path.join(project_root, 'data', 'phase12a_target_galex_v2.csv')
    control_file = os.path.join(project_root, 'data', 'phase12a_control_galex_v2.csv')
    
    if not os.path.exists(target_file) or not os.path.exists(control_file):
        print("❌ Missing Phase 12A crossmatch files.")
        return

    print("📥 Loading Phase 12A Matched Pairs...")
    targets = pd.read_csv(target_file)
    controls = pd.read_csv(control_file)
    print(f"🎯 Loaded {len(targets)} matched pairs for Multiplicity Crossmatch (V2).\n")

    # =========================================================================
    # 1. QUERY KNOWN MULTIPLICITY CATALOGS (MORPHEUS RADII)
    # =========================================================================
    print("📡 Querying VizieR for Known Multiplicity (WDS @ 10\", SB9 @ 3\")...")
    
    vizier = Vizier(columns=['*'])
    vizier.ROW_LIMIT = 5
    
    def check_known_binary(ra, dec):
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        in_wds = False
        in_sb9 = False
        
        try:
            # MORPHEUS FIX: 10 arcsec for WDS to catch wider visual binaries
            res_wds = vizier.query_region(coord, radius=10*u.arcsec, catalog="B/wds")
            if res_wds and len(res_wds) > 0 and len(res_wds[0]) > 0:
                in_wds = True
        except Exception:
            pass
            
        time.sleep(0.2)
        
        try:
            # SB9 remains 3 arcsec (spectroscopic binaries have precise coords)
            res_sb9 = vizier.query_region(coord, radius=3*u.arcsec, catalog="B/sb9")
            if res_sb9 and len(res_sb9) > 0 and len(res_sb9[0]) > 0:
                in_sb9 = True
        except Exception:
            pass
            
        return in_wds, in_sb9

    t_wds, t_sb9 = [], []
    c_wds, c_sb9 = [], []
    
    for i in range(len(targets)):
        tw, ts = check_known_binary(targets.iloc[i]['ra'], targets.iloc[i]['dec'])
        cw, cs = check_known_binary(controls.iloc[i]['ra'], controls.iloc[i]['dec'])
        
        t_wds.append(tw); t_sb9.append(ts)
        c_wds.append(cw); c_sb9.append(cs)
        
        t_status = get_status(tw, ts)
        c_status = get_status(cw, cs)
        
        print(f"   [{i+1}/{len(targets)}] Target: {t_status:<8} | Control: {c_status}")
        time.sleep(0.3) # Respect VizieR rate limits
        
    targets['in_wds'] = t_wds
    targets['in_sb9'] = t_sb9
    targets['known_multiple'] = targets['in_wds'] | targets['in_sb9']
    targets['multiplicity_type'] = [get_status(w, s) for w, s in zip(t_wds, t_sb9)]
    
    controls['in_wds'] = c_wds
    controls['in_sb9'] = c_sb9
    controls['known_multiple'] = controls['in_wds'] | controls['in_sb9']
    controls['multiplicity_type'] = [get_status(w, s) for w, s in zip(c_wds, c_sb9)]

    # =========================================================================
    # 2. STATISTICAL ANALYSIS (Fisher Exact Test)
    # =========================================================================
    print("\n" + "="*85)
    print("PHASE 12 PRIORITY 2 VERDICT: KNOWN MULTIPLICITY ENRICHMENT (V2)")
    print("="*85)
    
    t_mult = targets['known_multiple'].sum()
    c_mult = controls['known_multiple'].sum()
    
    print(f"Targets in WDS/SB9:  {t_mult}/{len(targets)} ({t_mult/len(targets)*100:.1f}%)")
    print(f"Controls in WDS/SB9: {c_mult}/{len(controls)} ({c_mult/len(controls)*100:.1f}%)")
    
    print("\n--- Multiplicity Type Breakdown (Targets) ---")
    print(targets['multiplicity_type'].value_counts())
    
    table = [[t_mult, len(targets) - t_mult], [c_mult, len(controls) - c_mult]]
    _, p_mult = fisher_exact(table, alternative='greater')
    print(f"\nFisher Exact p-value (Targets > Controls): {p_mult:.4e}\n")
    
    # =========================================================================
    # 3. FINAL MORPHEUS SYNTHESIS (Epistemologically Disciplined)
    # =========================================================================
    print("="*85)
    if p_mult < 0.05:
        print("🏆 KNOWN MULTIPLICITY ENRICHMENT DETECTED.")
        print("   The unexplained high-tension stars are significantly enriched in")
        print("   currently cataloged visual (WDS) and spectroscopic (SB9) binaries.")
        print("   This directly connects astrometric tension to unresolved multiplicity.")
    else:
        print("❌ NO ENRICHMENT IN CURRENTLY CATALOGED BINARIES.")
        print("   The targets are not preferentially represented in WDS or SB9.")
        print("   IMPORTANT: This does NOT mean they are single stars.")
        print("   WDS and SB9 are highly incomplete. This result remains entirely")
        print("   compatible with a population of previously uncataloged companions")
        print("   (e.g., faint M-dwarfs, brown dwarfs, or long-period planets)")
        print("   that have evaded traditional ground-based surveys.")
    print("="*85)
    
    # Save
    out_dir = os.path.join(project_root, 'data')
    targets.to_csv(os.path.join(out_dir, 'phase12_p2_target_multiplicity_v2.csv'), index=False)
    controls.to_csv(os.path.join(out_dir, 'phase12_p2_control_multiplicity_v2.csv'), index=False)
    print("💾 Saved V2 Multiplicity crossmatch results to data/")

if __name__ == "__main__":
    run_multiplicity_crossmatch_v2()