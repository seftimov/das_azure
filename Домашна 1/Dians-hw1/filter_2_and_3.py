import os
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from binance.client import Client as BinanceClient

# =======================
# CONFIG
# =======================
COINS_CSV = "top_1000_coins.csv"
HIST_DIR = "historical"
os.makedirs(HIST_DIR, exist_ok=True)

BINANCE_API_KEY = ""
BINANCE_API_SECRET = ""

SLEEP_SHORT = 0.1
SLEEP_LONG = 2.0

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart"


# =======================
# LOGGING
# =======================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# =======================
# FETCH FUNCTIONS
# =======================
def fetch_yahoo(symbol, since=None):
    try:
        df = yf.download(f"{symbol}-USD", period="max", interval="1d", progress=False, threads=False)
        if df is None or df.empty:
            return None
        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df[["date", "open", "high", "low", "close", "volume"]]
        if since is not None:
            df = df[df["date"] >= since]
        return df
    except Exception as e:
        log(f"Yahoo error for {symbol}: {e}")
        return None


def fetch_binance_spot(symbol, since=None):
    try:
        client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET)
        pair = f"{symbol.upper()}USDT"
        klines = client.get_historical_klines(pair, BinanceClient.KLINE_INTERVAL_1DAY, "10 years ago UTC")
        if not klines:
            return None
        df = pd.DataFrame(klines, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "q", "n", "tbb", "tbq", "ignore"
        ])
        df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.date
        df = df[["date", "open", "high", "low", "close", "volume"]]
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        if since is not None:
            df = df[df["date"] >= since]
        return df
    except Exception as e:
        log(f"Binance spot error for {symbol}: {e}")
        return None


def fetch_coingecko(coin_id, since=None):
    try:
        url = COINGECKO_URL.format(id=coin_id)
        r = requests.get(url, params={
            "vs_currency": "usd",
            "days": "365",
            "interval": "daily"
        }, timeout=30)

        if r.status_code != 200:
            return None

        data = r.json()
        prices = data.get("prices", [])
        if not prices:
            return None

        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
        df["open"] = df["price"]
        df["high"] = df["price"]
        df["low"] = df["price"]
        df["close"] = df["price"]

        vols = data.get("total_volumes", [])
        df["volume"] = [v[1] for v in vols] if vols else None

        df = df[["date", "open", "high", "low", "close", "volume"]]
        if since is not None:
            df = df[df["date"] >= since]
        return df
    except Exception as e:
        log(f"CoinGecko error: {e}")
        return None


# =======================
# TRY ALL SOURCES
# =======================
def try_all_sources(symbol, coin_id, since=None):
    df = fetch_yahoo(symbol, since)
    if df is not None and not df.empty:
        log(f"Data source: Yahoo Finance for symbol {symbol}, rows fetched: {len(df)}")
        return df
    else:
        log(f"Yahoo Finance returned no data or failed for symbol {symbol}")

    df = fetch_binance_spot(symbol, since)
    if df is not None and not df.empty:
        log(f"Data source: Binance Spot for symbol {symbol}, rows fetched: {len(df)}")
        return df
    else:
        log(f"Binance Spot returned no data or failed for symbol {symbol}")

    df = fetch_coingecko(coin_id, since)
    if df is not None and not df.empty:
        log(f"Data source: CoinGecko for coin_id {coin_id}, rows fetched: {len(df)}")
        return df
    else:
        log(f"CoinGecko returned no data or failed for coin_id {coin_id}")

    log(f"No data found from any source for symbol {symbol} / coin_id {coin_id}")
    return None


# =======================
# FILTER 2
# =======================
def filter2_get_last_date(coin_id):
    path = os.path.join(HIST_DIR, f"{coin_id}.csv")
    if not os.path.exists(path):
        log(f" - No CSV on disk for {coin_id}")
        return None
    try:
        df = pd.read_csv(path)
        if df.empty or "date" not in df.columns:
            log(f" - CSV for {coin_id} is empty or has no 'date' column")
            return None
        df["date"] = pd.to_datetime(df["date"], errors='coerce').dt.date
        df = df.dropna(subset=['date'])
        if df.empty:
            log(f" - CSV for {coin_id} has no valid dates after parsing")
            return None
        last = df["date"].max()
        log(f" - Latest date for {coin_id}: {last}")
        return last
    except Exception as e:
        log(f" - Exception reading {coin_id}.csv: {e}")
        return None


# =======================
# FILTER 3
# =======================
def filter3_download_missing(coin_id, symbol, last_date):
    """
    last_date = None → download full history
    last_date = date → download only from date + 1 day onward
    """
    if last_date is None:
        log(" - No existing history → full download")
        df = try_all_sources(symbol, coin_id, since=None)
        if df is None or df.empty:
            log(" - No data found")
            return False
        save_history(coin_id, df)
        return True

    since = last_date + timedelta(days=1)
    log(f" - Last date = {last_date}, need missing from {since}")
    df = try_all_sources(symbol, coin_id, since=since)

    if df is None or df.empty:
        log(" - No new rows")
        return True

    append_history(coin_id, df)
    return True


# =======================
# SAVE / APPEND FUNCTIONS
# =======================
def save_history(coin_id, df):
    path = os.path.join(HIST_DIR, f"{coin_id}.csv")
    df.to_csv(path, index=False)
    log(f"   Saved {coin_id} (full history, {len(df)} rows)")


def append_history(coin_id, df_new):
    path = os.path.join(HIST_DIR, f"{coin_id}.csv")
    df_old = pd.read_csv(path)
    df_old["date"] = pd.to_datetime(df_old["date"]).dt.date
    df_new["date"] = pd.to_datetime(df_new["date"]).dt.date

    combined = pd.concat([df_old, df_new], ignore_index=True)
    combined = combined.drop_duplicates(subset="date").sort_values("date")
    combined.to_csv(path, index=False)
    log(f"   Appended {len(df_new)} new rows → {coin_id}.csv")


# =======================
# PIPE: FILTER 1 → FILTER 2 → FILTER 3
# =======================
def main():
    start_time = datetime.now()
    coins = pd.read_csv(COINS_CSV, dtype=str)
    for i, row in coins.iterrows():
        coin_id = row["id"]
        symbol = row["symbol"].upper()
        log(f"[{i + 1}/{len(coins)}] {symbol} ({coin_id})")

        # --- FILTER 2: Get last date available
        last_date = filter2_get_last_date(coin_id)

        # --- FILTER 3: Download only missing data
        success = filter3_download_missing(coin_id, symbol, last_date)
        if not success:
            log(f"Failed to update {symbol}")
        time.sleep(SLEEP_SHORT)

    duration = datetime.now() - start_time
    log(f"=== ALL DONE === Total elapsed time: {duration}")


if __name__ == "__main__":
    main()
