import os
import pandas as pd

HIST_DIR = "historical"
OUTPUT = "all_coins.csv"

rows = []

for filename in os.listdir(HIST_DIR):
    if not filename.endswith(".csv"):
        continue

    coin_id = filename.replace(".csv", "")
    path = os.path.join(HIST_DIR, filename)

    df = pd.read_csv(path)
    df["coin_id"] = coin_id
    rows.append(df)

# merge
all_df = pd.concat(rows, ignore_index=True)
all_df = all_df.sort_values(["coin_id", "date"])
all_df.to_csv(OUTPUT, index=False)

print(f"Created {OUTPUT} with {len(all_df)} rows")
