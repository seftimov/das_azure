import requests
import pandas as pd
import time
from datetime import datetime

# === CONFIG ===
OUTPUT_JSON = "top_1000_coins.json"
OUTPUT_CSV = "top_1000_coins.csv"

MIN_VOLUME_USD = 100000
MAX_PAGES = 10  # 10 x 250 = 2500
RETRY_DELAY = 15  # seconds to wait on rate limit


def fetch_top_coins():
    print("Fetching data from CoinGecko...")

    all_coins = []
    for page in range(1, MAX_PAGES + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "sparkline": "false",
        }

        success = False
        for attempt in range(5):
            response = requests.get(url, params=params)
            if response.status_code == 200:
                success = True
                break
            elif response.status_code == 429:
                print(f"Rate limit hit (page {page}), waiting {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Error fetching page {page}: {response.status_code}")
                break

        if not success:
            print(f"Failed to fetch page {page} after retries. Skipping.")
            continue

        data = response.json()
        if not data:
            break

        for coin in data:
            all_coins.append({
                "id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "market_cap_rank": coin.get("market_cap_rank"),
                "current_price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "total_volume": coin.get("total_volume"),
                "last_updated": coin.get("last_updated"),
                "is_active": not coin.get("market_cap") is None
            })

        print(f"Page {page} fetched ({len(data)} coins)")
        time.sleep(2)

    print(f"\nTotal coins fetched: {len(all_coins)}")
    return all_coins


def filter_coins(coins):
    print("\nFiltering coins (valid + liquidity)...")
    df = pd.DataFrame(coins)

    df = df.drop_duplicates(subset="symbol", keep="first")
    df = df[df["is_active"] == True]
    df = df[df["total_volume"] >= MIN_VOLUME_USD]
    df = df.dropna(subset=["market_cap_rank"])
    df = df.sort_values(by="market_cap_rank").reset_index(drop=True)

    df = df.head(1500)

    print(f"Coins after filtering: {len(df)}")
    return df


def save_results(df):
    df.to_json(OUTPUT_JSON, orient="records", indent=2)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {len(df)} coins to:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_CSV}")


def main():
    print(f"=== Filter 1: Top 1000 Cryptocurrencies ===")
    start = datetime.now()

    coins = fetch_top_coins()
    df_filtered = filter_coins(coins)
    save_results(df_filtered)

    duration = datetime.now() - start
    print(f"\nCompleted in {duration.seconds} seconds.")


if __name__ == "__main__":
    main()
