import pandas as pd
from pathlib import Path
import mysql.connector

NEWS_DIR = Path("cryptonews_raw")
NEWS_DIR.mkdir(exist_ok=True)

CSV_PATH = NEWS_DIR / "news_currencies_source_joinedResult.csv"


def main():
    df = pd.read_csv(CSV_PATH)
    print("Original columns:", df.columns.tolist())
    print("Rows:", len(df))

    sentiment_cols = [
        "negative",
        "positive",
        "important",
        "liked",
        "disliked",
        "lol",
        "toxic",
        "saved",
        "comments",
    ]

    df_clean = df.drop(columns=sentiment_cols, errors="ignore")

    OUT_CLEAN = NEWS_DIR / "news_joined_clean_for_nlp.csv"
    df_clean.to_csv(OUT_CLEAN, index=False)
    print("\nClean NLP input saved to:", OUT_CLEAN.resolve())
    print("Kept columns:", df_clean.columns.tolist())

    print("\nExpanding currencies -> one row per (news, coin)...")
    rows = []
    for _, row in df_clean.iterrows():
        cur = str(row.get("currencies", ""))
        if not cur or cur.lower() == "nan":
            continue
        for code in cur.split(";"):
            code = code.strip().upper()
            if not code:
                continue
            r = row.copy()
            r["symbol"] = code
            rows.append(r)

    expanded = pd.DataFrame(rows)
    EXPANDED_PATH = NEWS_DIR / "news_expanded_by_coin.csv"
    expanded.to_csv(EXPANDED_PATH, index=False)
    print(f"Expanded rows: {len(expanded)}")
    print(f"Coins covered in news: {expanded['symbol'].nunique()}")
    print("Saved expanded file to:", EXPANDED_PATH.resolve())

    print("\nLoading target coins from MySQL (all symbols)...")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Test123!",
        database="crypto_data",
    )
    coins_df = pd.read_sql("SELECT symbol FROM coins", conn)
    conn.close()

    target = set(coins_df["symbol"].str.upper())
    print(f"Target coins from DB (unique symbols): {len(target)}")

    expanded = pd.read_csv(EXPANDED_PATH)
    expanded_filtered = expanded[expanded["symbol"].isin(target)].copy()

    FILTERED_PATH = NEWS_DIR / "news_expanded_filtered.csv"
    expanded_filtered.to_csv(FILTERED_PATH, index=False)
    print(f"Filtered rows: {len(expanded_filtered)} saved to {FILTERED_PATH.resolve()}")

    print("\nPreview:")
    print(expanded_filtered[["newsDatetime", "symbol", "title"]].head())


if __name__ == "__main__":
    main()
