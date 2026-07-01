import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("gaia_candidates.csv")

plt.figure(figsize=(8,6))
plt.scatter(df["ra"], df["dec"], s=5)

plt.xlabel("Right Ascension")
plt.ylabel("Declination")
plt.title("Gaia Candidate Sources")

plt.grid(True)

plt.savefig("candidate_map.png")
plt.show()