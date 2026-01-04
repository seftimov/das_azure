import pandas as pd
import requests
import mysql.connector
import numpy as np
from pathlib import Path
from tqdm import tqdm

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "Test123!"
DB_NAME = "crypto_data"

DOWNLOAD_DIR = Path("coinmetrics_csvs")
DOWNLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR = Path("coinmetrics_processed")
PROCESSED_DIR.mkdir(exist_ok=True)


def load_coins_from_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
        query = """
        SELECT coin_id, symbol, name, market_cap_rank 
        FROM coins 
        WHERE market_cap_rank IS NOT NULL 
        ORDER BY market_cap_rank 
        LIMIT 1200
        """
        coins_df = pd.read_sql(query, conn)
        conn.close()
        print(f"Loaded {len(coins_df)} coins from database")
        return coins_df
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        exit(1)


def compute_nvt_ratio(df):
    market_cap = df.get('CapMrktCurUSD', pd.Series([np.nan] * len(df)))
    tx_volume = df.get('volume_reported_spot_usd_1d', pd.Series([np.nan] * len(df)))

    nvt_ratio = np.where(
        (tx_volume > 0) & (market_cap > 0),
        market_cap / tx_volume,
        np.nan
    )

    df['NVT_Ratio'] = nvt_ratio
    return df


print("Loading coins from MySQL database...")
coins_df = load_coins_from_db()

coin_symbols = coins_df['symbol'].str.lower().tolist()
coin_ids = coins_df['coin_id'].tolist()

print(f"Found {len(coin_symbols)} coins in database")
BASE_URL = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/"

successful_downloads = 0
successful_processed = 0
failed_downloads = []
results = []

print("Downloading + Computing NVT Ratio...")
for symbol, coin_id in tqdm(zip(coin_symbols, coin_ids), total=len(coin_symbols)):
    csv_url = f"{BASE_URL}{symbol}.csv"
    raw_path = DOWNLOAD_DIR / f"{symbol}.csv"
    processed_path = PROCESSED_DIR / f"{symbol}_nvt.csv"

    if processed_path.exists():
        successful_processed += 1
        results.append({'symbol': symbol, 'coin_id': coin_id, 'status': 'processed'})
        continue

    if not raw_path.exists():
        try:
            response = requests.get(csv_url, timeout=10)
            if response.status_code != 200:
                failed_downloads.append({'symbol': symbol, 'coin_id': coin_id})
                results.append({'symbol': symbol, 'coin_id': coin_id, 'status': 'missing'})
                continue
            with open(raw_path, 'wb') as f:
                f.write(response.content)
            successful_downloads += 1
        except Exception:
            failed_downloads.append({'symbol': symbol, 'coin_id': coin_id})
            results.append({'symbol': symbol, 'coin_id': coin_id, 'status': 'error'})
            continue

    try:
        df_raw = pd.read_csv(raw_path)
        if len(df_raw) == 0:
            results.append({'symbol': symbol, 'coin_id': coin_id, 'status': 'empty'})
            continue

        df_processed = compute_nvt_ratio(df_raw)

        df_processed.to_csv(processed_path, index=False)
        successful_processed += 1
        results.append({'symbol': symbol, 'coin_id': coin_id, 'status': 'processed'})

    except Exception as e:
        results.append({'symbol': symbol, 'coin_id': coin_id, 'status': f'error: {str(e)[:30]}'})

results_df = pd.DataFrame(results)
results_df.to_csv(DOWNLOAD_DIR / "download_summary.csv", index=False)

print(f"\nNVT Processing complete!")
print(f"Raw files downloaded: {successful_downloads}")
print(f"Files with NVT_Ratio: {successful_processed}")
print(f"Missing: {len(failed_downloads)}")

print("\nMajor coins with NVT_Ratio:")
major_coins = ['btc', 'eth', 'xrp', 'sol', 'bnb']
for symbol in major_coins:
    raw_path = DOWNLOAD_DIR / f"{symbol}.csv"
    proc_path = PROCESSED_DIR / f"{symbol}_nvt.csv"
    if proc_path.exists():
        df_sample = pd.read_csv(proc_path)
        print(f"   {symbol}_nvt.csv (NVT_Ratio: {df_sample['NVT_Ratio'].mean():.1f} avg)")
    else:
        print(f"   {symbol}_nvt.csv")

print(f"\nRaw files: {DOWNLOAD_DIR.absolute()}")
print(f"NVT files: {PROCESSED_DIR.absolute()}")
print("Each *_nvt.csv has original columns + NVT_Ratio column!")
