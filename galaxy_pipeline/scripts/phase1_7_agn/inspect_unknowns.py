import pandas as pd
df = pd.read_csv("unknown_candidates.csv")
print(df.head(10))
print()
print("Count =", len(df))