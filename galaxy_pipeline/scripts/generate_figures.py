import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Ensure figures directory exists
import os
os.makedirs("figures", exist_ok=True)

# Load ranked candidates
df = pd.read_csv("data/batch_ranked_candidates.csv")

# ──────────────────────────────────────────────────────────────
# FIGURE 1: Pipeline Flowchart
# ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 9))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

steps = [
    ("Gaia DR3 Initial Query\n(500 Raw Sources)", 0.82),
    ("Astrometric Filters\n(PM/Parallax SNR < 3)", 0.68),
    ("Pan-STARRS Morphology\n(Δ(PSF−Kron) > 0.5)", 0.54),
    ("Color & ML Scoring\n(g−r < 0.5, DSC Prob)", 0.40),
    ("Tier Assignment & Ranking\n(T1 / T2 / T3 / T0)", 0.26),
    ("Final Catalog Export\n(24 Validated Candidates)", 0.12)
]

for i, (text, y) in enumerate(steps):
    rect = plt.Rectangle((1.5, y), 7, 0.10, facecolor="#e3f2fd", edgecolor="#1976d2", lw=2)
    ax.add_patch(rect)
    ax.text(5, y + 0.05, text, ha="center", va="center", fontsize=10, fontweight="bold")
    if i < len(steps) - 1:
        next_y = steps[i+1][1]
        ax.annotate("", xy=(5, next_y + 0.10), xytext=(5, y),
                    arrowprops=dict(arrowstyle="->", color="#1976d2", lw=2))

plt.tight_layout()
plt.savefig("figures/pipeline_flowchart.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Saved figures/pipeline_flowchart.png")

# ──────────────────────────────────────────────────────────────
# FIGURE 2: Score Distribution Histogram
# ──────────────────────────────────────────────────────────────
plt.figure(figsize=(8, 5))
plt.hist(df["priority_score"], bins=range(-2, 11), edgecolor="black", color="#4a90e2", alpha=0.8)
plt.xlabel("Priority Score", fontsize=12)
plt.ylabel("Number of Candidates", fontsize=12)
plt.title("Candidate Score Distribution", fontsize=14)
plt.xticks(range(-2, 11))
plt.grid(axis="y", linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig("figures/score_distribution.png", dpi=150)
plt.close()
print("✅ Saved figures/score_distribution.png")

# ──────────────────────────────────────────────────────────────
# FIGURE 3: Tier Breakdown Pie Chart
# ──────────────────────────────────────────────────────────────
tier_counts = df["tier"].value_counts().sort_index()
colors = ["#2ecc71", "#3498db", "#f1c40f", "#e74c3c"]  # T1, T2, T3, T0
plt.figure(figsize=(8, 5))
plt.pie(tier_counts, labels=tier_counts.index, autopct="%1.1f%%", startangle=140,
        colors=colors, wedgeprops=dict(edgecolor="white", lw=2))
plt.title("Tier Breakdown", fontsize=14)
plt.tight_layout()
plt.savefig("figures/tier_breakdown.png", dpi=150)
plt.close()
print("✅ Saved figures/tier_breakdown.png")

# ──────────────────────────────────────────────────────────────
# FIGURE 4: Extension vs. Priority Score Scatter
# ──────────────────────────────────────────────────────────────
# Extract numeric extension from strings like "Δ=1.18"
df["ext_numeric"] = df["ps1_extension"].str.extract(r"Δ=([0-9.]+)").astype(float)

plt.figure(figsize=(8, 5))
tiers = df["tier"].unique()
colors_map = {"T1_STRONG_GALAXY": "#2ecc71", "T2_PROBABLE_GALAXY": "#3498db", 
              "T3_AMBIGUOUS": "#f1c40f", "T0_REJECTED": "#e74c3c"}

for tier in tiers:
    subset = df[df["tier"] == tier]
    plt.scatter(subset["ext_numeric"], subset["priority_score"], 
                label=tier, color=colors_map.get(tier, "gray"), alpha=0.8, edgecolors="w", lw=0.5)

plt.xlabel("PSF−Kron Extension (Δ)", fontsize=12)
plt.ylabel("Priority Score", fontsize=12)
plt.title("Morphology Extension vs. Priority Score", fontsize=14)
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("figures/extension_vs_score.png", dpi=150)
plt.close()
print("✅ Saved figures/extension_vs_score.png")

print("\n📊 Figures 1–4 generated successfully.")