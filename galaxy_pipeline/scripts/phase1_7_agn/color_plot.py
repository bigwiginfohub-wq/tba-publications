import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("gaia_candidates.csv")

plt.figure(figsize=(8,6))

plt.scatter(
    df["bp_rp"],
    df["phot_g_mean_mag"],
    s=10
)

plt.gca().invert_yaxis()

plt.xlabel("BP - RP")
plt.ylabel("G Magnitude")
plt.title("Gaia Color-Magnitude Diagram")

plt.show()