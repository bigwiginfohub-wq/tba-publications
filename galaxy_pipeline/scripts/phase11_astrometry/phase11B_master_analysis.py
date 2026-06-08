import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

def run_phase11b_master():
    input_file = 'data/tracebind_master_catalog_v1.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    bench = df[df['anomaly_class'] != 'Below Top 5% Threshold'].copy()
    unknowns = bench[bench['anomaly_class'] == 'Unexplained Astrometric Tension (High Priority)']
    explained = bench[bench['anomaly_class'] != 'Unexplained Astrometric Tension (High Priority)']
    
    print(f"📋 Loaded Master Catalog ({len(df):,} total, {len(bench):,} benchmark anomalies).")
    print(f"   -> Unexplained: {len(unknowns):,} | Explained: {len(explained):,}\n")

    os.makedirs('figures', exist_ok=True)

    # =========================================================================
    # 11B.1: GALACTIC SKY MAP (Rule out crowding/systematics)
    # =========================================================================
    print("🌌 Plotting 11B.1: Galactic Sky Map...")
    fig = plt.figure(figsize=(14, 7))
    ax = fig.add_subplot(111, projection='mollweide')
    
    def plot_mollweide(ax, data, color, label, s, alpha):
        l_rad = np.radians(data['gal_l'])
        l_rad = np.where(l_rad > np.pi, l_rad - 2*np.pi, l_rad)
        b_rad = np.radians(data['gal_b'])
        ax.scatter(l_rad, b_rad, c=color, s=s, alpha=alpha, label=label, edgecolors='none')

    plot_mollweide(ax, explained, 'gray', 'Explained (NSS/Artifacts)', 10, 0.2)
    plot_mollweide(ax, unknowns, 'red', 'Unexplained Tension', 30, 0.8)
    
    ax.set_title('TRACEBIND 11B.1: Galactic Distribution of Astrometric Anomalies', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower left', fontsize=12, markerscale=3)
    plt.savefig('figures/11b_1_galactic_sky_map.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✅ Saved figures/11b_1_galactic_sky_map.png")

    # =========================================================================
    # 11B.2: HR DIAGRAM DENSITY PLOT (Identify stellar population hypothesis)
    # =========================================================================
    print("📊 Plotting 11B.2: HR Diagram Density...")
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Background: All stars in the master catalog (gray density)
    ax.scatter(df['bp_rp'], df['M_G'], c='lightgray', s=2, alpha=0.1, rasterized=True)
    
    # Foreground: Explained Anomalies (blue/green)
    ax.scatter(explained['bp_rp'], explained['M_G'], c='royalblue', s=15, alpha=0.4, label='Explained (NSS/Artifacts)')
    
    # Focus: Unexplained Anomalies (red)
    ax.scatter(unknowns['bp_rp'], unknowns['M_G'], c='red', s=35, alpha=0.8, edgecolors='black', linewidths=0.5, label='Unexplained Tension')
    
    ax.invert_yaxis()
    ax.set_xlabel('Gaia BP-RP Color (mag)', fontsize=14)
    ax.set_ylabel('Absolute Magnitude ($M_G$)', fontsize=14)
    ax.set_title('TRACEBIND 11B.2: HR Diagram of Astrometric Anomalies', fontsize=16, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.4)
    plt.savefig('figures/11b_2_hr_density.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✅ Saved figures/11b_2_hr_density.png")

    # =========================================================================
    # 11B.3: DR4 NSS-LIKELIHOOD RANKING ENGINE (Cross-Validated)
    # =========================================================================
    print("\n🧠 11B.3: Training Cross-Validated NSS-Likelihood Ranking Models...")
    
    # Define Feature Sets (Morpheus Ablation Study)
    feat_A = ['ruwe', 'astrometric_excess_noise']
    feat_B = ['tension_score']
    feat_C = ['ruwe', 'astrometric_excess_noise', 'tension_score', 'bp_rp', 'M_G', 'vt_kms', 'distance_pc', 'gal_b']
    
    target = 'in_any_nss'
    ml_df = df.dropna(subset=feat_C + [target]).copy()
    ml_df[target] = ml_df[target].astype(int)
    
    X_A, X_B, X_C = ml_df[feat_A], ml_df[feat_B], ml_df[feat_C]
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
        print(f"   {name:<15} | Mean ROC-AUC: {mean_auc:.4f} ± {std_auc:.4f}")
        return mean_auc

    print("   Running 5-Fold Stratified Cross-Validation...")
    evaluate_model(X_A, y, "Model A (Raw)")
    evaluate_model(X_B, y, "Model B (Tension)")
    auc_C = evaluate_model(X_C, y, "Model C (Full)")

    # Train Final Model C on ALL data to generate the ranked catalog
    print("\n   Training Final Model C on full dataset for ranking...")
    final_rf = RandomForestClassifier(**rf_params)
    final_rf.fit(X_C, y)
    
    # Predict NSS-Likelihood for ALL stars in the master catalog
    valid_mask = df[feat_C].notna().all(axis=1)
    df.loc[valid_mask, 'nss_likelihood'] = final_rf.predict_proba(df.loc[valid_mask, feat_C])[:, 1]
    
    # Isolate currently non-NSS stars and RANK them (No arbitrary 0.5 threshold)
    future_candidates = df[(df['in_any_nss'] == False) & (df['nss_likelihood'].notna())].copy()
    future_candidates = future_candidates.sort_values('nss_likelihood', ascending=False)
    
    export_cols = ['source_id', 'ra', 'dec', 'distance_pc', 'bp_rp', 'M_G', 
                   'ruwe', 'tension_score', 'nss_likelihood', 'anomaly_class']
    
    os.makedirs('data', exist_ok=True)
    out_file = 'data/tracebind_dr4_nss_likelihood_ranked.csv'
    future_candidates[export_cols].to_csv(out_file, index=False)
    
    print(f"\n   ✅ Saved Ranked Catalog to {out_file}")
    print(f"   -> Top 100 Likelihood: {future_candidates['nss_likelihood'].head(100).min():.4f}")
    print(f"   -> Top 500 Likelihood: {future_candidates['nss_likelihood'].head(500).min():.4f}")
    print(f"   -> Top 1000 Likelihood: {future_candidates['nss_likelihood'].head(1000).min():.4f}")
    
    print("\n" + "="*85)
    print("MORPHEUS VERDICT: 11B.1 - 11B.3 COMPLETE")
    print("="*85)
    print("1. Sky Map: Check if red dots avoid the Galactic Plane (rules out crowding).")
    print("2. HR Diagram: Check if red dots cluster on the lower main sequence (M-dwarf hypothesis).")
    print("3. ML Engine: Check if Model C (Full) outperforms Model A (Raw) and Model B (Tension).")
    print("   If yes, the composite metric and astrophysical context provide maximum predictive power.")
    print("="*85)

if __name__ == "__main__":
    run_phase11b_master()