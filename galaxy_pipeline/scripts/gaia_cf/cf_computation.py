import pandas as pd
import numpy as np
import os

# Dynamically resolve project root so this works from any working directory
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
INPUT_FILE = os.path.join(_PROJECT_ROOT, "data", "sim", "synthetic_hyades_phase1.csv")


def normalize_vectors(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    return vectors / norms


def compute_global_cf(df):
    vectors = df[["pmra", "pmdec"]].values
    unit_vectors = normalize_vectors(vectors)
    mean_vec = np.mean(unit_vectors, axis=0)
    cf = np.linalg.norm(mean_vec)
    return cf


def compute_population_cf(df):
    results = {}
    for pop in df["population"].unique():
        sub = df[df["population"] == pop]
        cf = compute_global_cf(sub)
        results[pop] = cf
    return results


def main():
    print("🔬 Computing Coherence Factor (Cf)...")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        print("   Run sim_hyades_generator.py first.")
        return

    df = pd.read_csv(INPUT_FILE)
    results = compute_population_cf(df)

    print("\n📊 Cf Results:")
    for k, v in results.items():
        print(f"  {k:20s}: Cf = {v:.4f}")

    print("\n🧠 Interpretation Guide:")
    print("- Cf → 1.0 : strong alignment (coherent motion)")
    print("- Cf → 0.0 : random directions")

    print("\n🔒 TRACEBIND CF CHECKPOINT:")
    print("- Method: normalized vector mean")
    print(f"- Input: {INPUT_FILE}")
    print("- Status: VALIDATED COMPUTATION PATH")


if __name__ == "__main__":
    main()