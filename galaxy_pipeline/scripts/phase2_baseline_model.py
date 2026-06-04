import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

print("="*60)
print("PHASE 2: STATISTICAL SEPARATION & BASELINE ML")
print("="*60)

# 1. Load the datasets
print("\n[1/4] Loading Background (Random Sky)...")
bg = pd.read_csv('gaia_phase1_scaled_10k.csv')
print("[2/4] Loading Signal (Final Candidates)...")
signal = pd.read_csv('gaia_phase1_final_candidates.csv')

# 2. Define the features we care about
features = ['phot_g_mean_mag', 'bp_rp', 'ruwe', 'parallax', 'pmra', 'pmdec']

# Drop rows with missing values in these specific columns
bg = bg.dropna(subset=features)
signal = signal.dropna(subset=features)

# 3. Create labels
bg['label'] = 0
signal['label'] = 1
df = pd.concat([bg, signal], ignore_index=True)

print(f"\nDataset combined: {len(df)} total sources.")
print(f"Normal Stars (0): {len(bg)}")
print(f"Rare Anomalies (1): {len(signal)}")

# =====================================================================
# PART A: STANDARDIZED SEPARATION (Z-SCORE ANALYSIS)
# This is the most scientifically honest way to see what separates the groups
# =====================================================================
print("\n" + "="*60)
print("PART A: STANDARDIZED SEPARATION (Z-Score)")
print("How many standard deviations away from the 'Normal' background is the 'Signal'?")
print("="*60)

bg_means = bg[features].mean()
bg_stds = bg[features].std()
signal_means = signal[features].mean()

z_scores = (signal_means - bg_means) / bg_stds

# Sort by absolute magnitude of separation
z_scores_abs = z_scores.abs().sort_values(ascending=False)

for feat in z_scores_abs.index:
    z = z_scores[feat]
    bar_len = int(abs(z) * 5)
    bar = '█' * bar_len
    direction = "+" if z > 0 else "-"
    print(f"{feat:20s}: {z:+.3f} σ  {direction}{bar}")

# =====================================================================
# PART B: STRATIFIED K-FOLD CROSS-VALIDATION
# A more honest evaluation than a single train/test split
# =====================================================================
print("\n" + "="*60)
print("PART B: STRATIFIED 5-FOLD CROSS-VALIDATION")
print("="*60)

X = df[features]
y = df['label']

rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# We use F1 score because accuracy is useless in extreme imbalance
f1_scores = cross_val_score(rf, X, y, cv=cv, scoring='f1')

print(f"Fold F1 Scores: {[f'{s:.3f}' for s in f1_scores]}")
print(f"Mean F1 Score:  {f1_scores.mean():.3f} (+/- {f1_scores.std():.3f})")
print("(Note: High F1 here means the model easily separates the selection criteria, not necessarily that it discovers new physics.)")

# =====================================================================
# PART C: FEATURE IMPORTANCE
# =====================================================================
print("\n" + "="*60)
print("PART C: RANDOM FOREST FEATURE IMPORTANCE")
print("="*60)

# Train on full dataset just to extract the global feature importances
rf.fit(X, y)
importances = sorted(zip(features, rf.feature_importances_), key=lambda x: x[1], reverse=True)

for feat, imp in importances:
    bar = '█' * int(imp * 50)
    print(f"{feat:20s}: {imp:.4f} {bar}")

print("="*60)
print("PHASE 2 BASELINE COMPLETE.")
print("The Z-scores reveal the true astrophysical separation.")
print("="*60)