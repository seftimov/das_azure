import requests
from pathlib import Path
import patoolib

NEWS_DIR = Path("cryptonews_raw")
NEWS_DIR.mkdir(exist_ok=True)

RAR_URL = "https://github.com/soheilrahsaz/cryptoNewsDataset/raw/main/csvOutput/news_currencies_source_joinedResult.rar"
RAR_PATH = NEWS_DIR / "news_joined.rar"


def main():
    print("Downloading joined news RAR...")
    resp = requests.get(RAR_URL, timeout=120)
    resp.raise_for_status()

    with open(RAR_PATH, "wb") as f:
        f.write(resp.content)

    print(f"Saved RAR to: {RAR_PATH.resolve()}")

    print("Auto-extracting RAR...")
    patoolib.extract_archive(str(RAR_PATH), outdir=NEWS_DIR)
    print("News CSV extracted successfully!")


if __name__ == "__main__":
    main()
