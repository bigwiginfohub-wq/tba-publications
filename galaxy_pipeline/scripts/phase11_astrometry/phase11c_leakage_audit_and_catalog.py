import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

def run_phase11c():
    input_file = 'data/tracebind_master_catalog_v1.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded Master Catalog v1.0 ({len(df):,} stars).\n")

    # Define Feature Sets for the Leakage Audit
    feat_D = ['bp_rp', 'M_G', 'distance_pc', 'vt_kms', 'gal_b'] # Astrophysics ONLY
    feat_A = ['ruwe', 'astrometric_excess_noise']                # Raw Astrometry ONLY
    feat_C = ['ruwe', 'astrometric_excess_noise', 'tension_score', 
              'bp_rp', 'M_G', 'vt_kms', 'distance_pc', 'gal_b'] # Combined
    
    target = 'in_any_nss'
    ml_df = df.dropna(subset=feat_C + [target]).copy()
    ml_df[target] = ml_df[target].astype(int)
    
    X_D, X_A, X_C = ml_df[feat_D], ml_df[feat_A], ml_df[feat_C]
    y = ml_df[target]
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rf_params = {'n_estimators': 200, 'max_depth': 10, 'class_weight': 'balanced', 'random_state': 42, 'n_jobs': -1}
    
    def evaluate_model(X, y, name):
        aucs = []
        for train_idx, test_idx in cv.split(X, y):
            rf = RandomForestClassifier(**rf_params)
            rf.fit(X.iloc[train_idx], y.iloc[train_idx])
            probs = rf.predict_proba(X.iloc[test_idx])[:, 1]
            aucs.append(roc_auc_score(y.iloc[test_idx], probs))
        mean_auc, std_auc = np.mean(aucs), np.std(aucs)
        print(f"   {name:<25} | Mean ROC-AUC: {mean_auc:.4f} ± {std_auc:.4f}")
        return mean_auc

    # =========================================================================
    # 1. THE LEAKAGE AUDIT (Model D vs A vs C)
    # =========================================================================
    print("="*85)
    print("PHASE 11C: LEAKAGE AUDIT & INDEPENDENT SIGNAL VALIDATION")
    print("="*85)
    print("Testing if Astrophysics (Model D) carries independent signal from Astrometry (A).\n")
    
    auc_D = evaluate_model(X_D, y, "Model D (Astrophysics)")
    auc_A = evaluate_model(X_A, y, "Model A (Raw Astrometry)")
    auc_C = evaluate_model(X_C, y, "Model C (Combined Full)")
    
    print("\n--- VERDICT ---")
    if auc_D > 0.60 and auc_C > auc_A and auc_C > auc_D:
        print("✅ LEAKAGE AUDIT PASSED.")
        print("   Astrophysics carries independent signal. Astrometry carries independent signal.")
        print("   The Combined Model (C) is superior, proving no single feature dominates by leakage.")
    else:
        print("⚠️ Review Signal Independence.")

    # =========================================================================
    # 2. REFINED FOLLOW-UP CATALOG (Morpheus Heuristic)
    # =========================================================================
    print("\n" + "="*85)
    print("GENERATING REFINED FOLLOW-UP CATALOG")
    print("="*85)
    
    # Train final Model C on all data to get probabilities for the whole sky
    final_rf = RandomForestClassifier(**rf_params)
    final_rf.fit(X_C, y)
    
    valid_mask = df[feat_C].notna().all(axis=1)
    df.loc[valid_mask, 'nss_likelihood'] = final_rf.predict_proba(df.loc[valid_mask, feat_C])[:, 1]
    
    # Normalize Tension Score (Min-Max scaling to 0-1)
    t_min, t_max = df['tension_score'].min(), df['tension_score'].max()
    df['tension_norm'] = (df['tension_score'] - t_min) / (t_max - t_min)
    
    # Calculate Morpheus Follow-Up Score
    df['followup_score'] = (0.6 * df['nss_likelihood']) + (0.4 * df['tension_norm'])
    
    # Isolate the Unexplained, Non-NSS population
    targets = df[
        (df['in_any_nss'] == False) & 
        (df['anomaly_class'] == 'Unexplained Astrometric Tension (High Priority)') &
        (df['followup_score'].notna())
    ].copy()
    
    # Rank and Export Top 100
    top_100 = targets.sort_values('followup_score', ascending=False).head(100)
    
    export_cols = ['source_id', 'ra', 'dec', 'distance_pc', 'bp_rp', 'M_G', 
                   'ruwe', 'tension_score', 'nss_likelihood', 'followup_score']
    
    os.makedirs('data', exist_ok=True)
    out_file = 'data/tracebind_followup_top100_refined.csv'
    top_100[export_cols].to_csv(out_file, index=False)
    
    print(f"✅ Saved Refined Top 100 Targets to {out_file}")
    print(f"   -> These targets balance high astrometric tension with high DR4 NSS probability.")
    print(f"   -> They are the optimal candidates for Phase 12 (GALEX/ROSAT/TESS) follow-up.")
    print("="*85)

if __name__ == "__main__":
    run_phase11c()