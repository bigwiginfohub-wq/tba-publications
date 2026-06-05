import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
import os

def run_advanced_regression():
    input_file = 'data/sandbox_coefficient_sweep_results.csv'
    if not os.path.exists(input_file):
        print(f"❌ Could not find {input_file}.")
        return

    df = pd.read_csv(input_file)
    print(f"📋 Loaded {len(df)} sweep scenarios for Advanced Regression Analysis.\n")

    # REVIEWER FIX #4: Use mean_theta_deg instead of max_theta_deg for stability
    target = 'mean_theta_deg' 
    
    print("="*80)
    print(f"      MODEL 1: MAIN EFFECTS ONLY (Target: {target})")
    print("="*80)
    model_main = smf.ols(f'{target} ~ alpha + beta + gamma', data=df)
    results_main = model_main.fit()
    
    print(f"   R-squared:          {results_main.rsquared:.4f}")
    print(f"   Adjusted R-squared: {results_main.rsquared_adj:.4f}\n")

    print("="*80)
    print(f"      MODEL 2: MAIN EFFECTS + PARAMETER COUPLING")
    print("="*80)
    model_inter = smf.ols(f'{target} ~ alpha + beta + gamma + alpha:beta + alpha:gamma + beta:gamma', data=df)
    results_inter = model_inter.fit()
    
    print(f"   R-squared:          {results_inter.rsquared:.4f}")
    print(f"   Adjusted R-squared: {results_inter.rsquared_adj:.4f}\n")

    # REVIEWER FIX #6: Formal Comparison
    print("--- MODEL COMPARISON ---")
    delta_adj_r2 = results_inter.rsquared_adj - results_main.rsquared_adj
    print(f"   Δ Adjusted R²:      {delta_adj_r2:+.4f}")
    if delta_adj_r2 > 0.05:
        print("   ✅ Adding interaction terms significantly improves the model's explanatory power.")
    else:
        print("   ⚠️ Interaction terms do not provide enough explanatory gain to justify the added complexity.")

    # REVIEWER FIX #5 & #2: Extract Coefficients and P-values (Focusing on Effect Size)
    print("\n--- COEFFICIENT ATTRIBUTION (Effect Sizes) ---")
    print(f"{'Term':<15} | {'Coefficient':>12} | {'P-value':>10} | {'Interpretation'}")
    print("-" * 75)
    
    terms_to_check = ['alpha', 'beta', 'gamma', 'alpha:beta', 'alpha:gamma', 'beta:gamma']
    for term in terms_to_check:
        if term in results_inter.params:
            coef = results_inter.params[term]
            pval = results_inter.pvalues[term]
            sig = "✅ Strong" if pval < 0.05 else ("⚠️ Moderate" if pval < 0.10 else "❌ Weak")
            print(f"{term:<15} | {coef:>12.3f} | {pval:>10.4f} | {sig}")

    # REVIEWER FIX #3: Multicollinearity Check (VIF)
    print("\n--- MULTICOLLINEARITY CHECK (Variance Inflation Factor) ---")
    X_inter = results_inter.model.exog
    vif_data = pd.DataFrame({
        "Feature": results_inter.model.exog_names,
        "VIF": [variance_inflation_factor(X_inter, i) for i in range(X_inter.shape[1])]
    })
    
    for _, row in vif_data.iterrows():
        if row['Feature'] == 'Intercept': continue
        vif_val = row['VIF']
        status = "✅ OK" if vif_val < 5 else ("⚠️ High" if vif_val < 10 else "🚨 Severe Multicollinearity")
        print(f"   {row['Feature']:<15} VIF = {vif_val:>6.2f}  {status}")
        
    print("\n" + "="*80)
    print("      DIAGNOSTIC VERDICT")
    print("="*80)
    print("Look at the interaction coefficients (alpha:beta, alpha:gamma, beta:gamma).")
    print("If they are large and statistically strong, the model's geometry is governed")
    print("by parameter coupling, exactly as the reviewer hypothesized.")
    print("="*80)

if __name__ == "__main__":
    run_advanced_regression()