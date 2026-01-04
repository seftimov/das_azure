import requests
from pathlib import Path

NEWS_DIR = Path("cryptonews_raw")
NEWS_DIR.mkdir(exist_ok=True)

RAR_URL = "https://github.com/soheilrahsaz/cryptoNewsDataset/raw/main/csvOutput/news_currencies_source_joinedResult.rar"
RAR_PATH = NEWS_DIR / "news_joined.rar"

print("Downloading joined news RAR...")
resp = requests.get(RAR_URL, timeout=120)
resp.raise_for_status()

with open(RAR_PATH, "wb") as f:
    f.write(resp.content)

print(f"Saved RAR to: {RAR_PATH.resolve()}")
print("Now unzip this RAR manually. In the next script we will load the CSV and drop sentiment columns.")
