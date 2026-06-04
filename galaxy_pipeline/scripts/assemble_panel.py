import matplotlib.pyplot as plt
import matplotlib.image as mpimg

fig, axes = plt.subplots(1, 2, figsize=(10, 5))

axes[0].imshow(mpimg.imread("figures/ps1_cutout.png"))
axes[0].set_title("Pan-STARRS DR2 (grz)")
axes[0].axis("off")

axes[1].imshow(mpimg.imread("figures/legacy_cutout.png"))
axes[1].set_title("Legacy Survey DR10 (grz)")
axes[1].axis("off")

fig.suptitle("Top Candidate: Gaia DR3 4575090461821845760", fontsize=14, fontweight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("figures/top_candidate_panel.png", dpi=150)
plt.close()
print("✅ Saved figures/top_candidate_panel.png")