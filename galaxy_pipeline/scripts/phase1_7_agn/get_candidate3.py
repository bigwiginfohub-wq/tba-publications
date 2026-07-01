import pandas as pd

df = pd.read_csv("unknown_candidates.csv")

# Match with tight tolerance to avoid float precision errors
match = df[
    (abs(df["ra"] - 204.992453) < 0.0001) & 
    (abs(df["dec"] - 0.834006) < 0.0001)
]

if match.empty:
    print("NO MATCH FOUND. Check CSV column names or coordinates.")
else:
    print("CANDIDATE 3 FULL DATA:")
    print(match.to_string(index=False))
    
    # Extract source_id safely (handle scientific notation if present)
    sid = int(float(match["source_id"].values[0]))
    print(f"\nSOURCE_ID FOR GAIA QUERY: {sid}")