import pandas as pd
from pathlib import Path

# Paths
ONCHAIN_PATH = Path("merged_data") / "master_onchain_merged.csv"  # adjust if name differs
SENT_PATH = Path("nlp") / "daily_sentiment_per_coin.csv"

OUTPUT_DIR = Path("on_chain_sentiment_merge")
OUTPUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUTPUT_DIR / "onchain_with_sentiment.csv"

# 1) Load on-chain data
onchain = pd.read_csv(ONCHAIN_PATH)
print("On-chain rows:", len(onchain))

# Normalize date + symbol
onchain["date"] = pd.to_datetime(onchain["time"]).dt.date
onchain["symbol"] = onchain["symbol"].str.upper()

# 2) Load daily sentiment
sent = pd.read_csv(SENT_PATH)
sent["date"] = pd.to_datetime(sent["date"]).dt.date
sent["symbol"] = sent["symbol"].str.upper()

print("Sentiment rows:", len(sent))

# 3) Merge on (symbol, date)
merged = onchain.merge(
    sent,
    on=["symbol", "date"],
    how="left"  # keep all on-chain rows
)

print("Merged rows:", len(merged))
print("Merged columns:", merged.columns.tolist()[:20])

# 4) Save merged file
merged.to_csv(OUT_PATH, index=False)
print("Saved merged file:", OUT_PATH.resolve())
