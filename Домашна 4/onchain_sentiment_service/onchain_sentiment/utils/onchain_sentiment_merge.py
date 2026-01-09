import pandas as pd
from pathlib import Path
import numpy as np
import mysql.connector

ONCHAIN_PATH = Path("merged_data") / "master_onchain_merged.csv"
SENT_PATH = Path("nlp") / "daily_sentiment_per_coin.csv"

OUTPUT_DIR = Path("on_chain_sentiment_merge")
OUTPUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUTPUT_DIR / "onchain_with_sentiment.csv"

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "Test123!"
DB_NAME = "crypto_data"


def main():
    onchain = pd.read_csv(ONCHAIN_PATH)
    sent = pd.read_csv(SENT_PATH)

    print("On-chain rows:", len(onchain))
    print("Sentiment rows:", len(sent))

    onchain["time"] = pd.to_datetime(onchain["time"], errors="coerce")
    onchain["date"] = onchain["time"].dt.date
    onchain["symbol"] = onchain["symbol"].str.upper()

    sent["date"] = pd.to_datetime(sent["date"]).dt.date
    sent["symbol"] = sent["symbol"].str.upper()

    merged = onchain.merge(sent, on=["symbol", "date"], how="left")

    print("Merged rows:", len(merged))

    for col in ["AssetCompletionTime", "AssetEODCompletionTime"]:
        if col in merged.columns:
            merged[col] = pd.to_datetime(merged[col], errors="coerce", unit="s")

    merged.to_csv(OUT_PATH, index=False)
    print("Saved:", OUT_PATH.resolve())

    def insert_to_db(df, batch_size=2000):
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            autocommit=True
        )
        cursor = conn.cursor()

        sql = """
        INSERT INTO onchain_metrics_test (
            symbol, date, time,
            CapMrktEstUSD, ReferenceRate, ReferenceRateBTC,
            ReferenceRateETH, ReferenceRateEUR, ReferenceRateUSD,
            volume_reported_spot_usd_1d, NVT_Ratio,
            AdrActCnt, AdrBalCnt,
            AssetCompletionTime, AssetEODCompletionTime,
            CapMVRVCur, CapMrktCurUSD,
            IssTotNtv, IssTotUSD,
            PriceBTC, PriceUSD,
            ROI1yr, ROI30d,
            SplyCur,
            TxCnt, TxTfrCnt, BlkCnt,
            FeeTotNtv, HashRate,
            SplyExpFut10yr,
            FlowInExNtv, FlowInExUSD,
            FlowOutExNtv, FlowOutExUSD,
            SplyExNtv, SplyExUSD,
            sentiment_score
        )
        VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s
        )
        ON DUPLICATE KEY UPDATE
            time = VALUES(time),
            PriceUSD = VALUES(PriceUSD),
            sentiment_score = VALUES(sentiment_score)
        """

        df = df.replace({np.nan: None})

        total = len(df)
        print(f"Inserting {total:,} rows...")

        for start in range(0, total, batch_size):
            end = start + batch_size
            batch = df.iloc[start:end]

            rows = [
                (
                    r.symbol, r.date, r.time,
                    r.CapMrktEstUSD, r.ReferenceRate, r.ReferenceRateBTC,
                    r.ReferenceRateETH, r.ReferenceRateEUR, r.ReferenceRateUSD,
                    r.volume_reported_spot_usd_1d, r.NVT_Ratio,
                    r.AdrActCnt, r.AdrBalCnt,
                    r.AssetCompletionTime, r.AssetEODCompletionTime,
                    r.CapMVRVCur, r.CapMrktCurUSD,
                    r.IssTotNtv, r.IssTotUSD,
                    r.PriceBTC, r.PriceUSD,
                    r.ROI1yr, r.ROI30d,
                    r.SplyCur,
                    r.TxCnt, r.TxTfrCnt, r.BlkCnt,
                    r.FeeTotNtv, r.HashRate,
                    r.SplyExpFut10yr,
                    r.FlowInExNtv, r.FlowInExUSD,
                    r.FlowOutExNtv, r.FlowOutExUSD,
                    r.SplyExNtv, r.SplyExUSD,
                    r.sentiment_score
                )
                for r in batch.itertuples(index=False)
            ]

            cursor.executemany(sql, rows)
            print(f"  Inserted rows {start:,} -> {min(end, total):,}")

        cursor.close()
        conn.close()
        print("All data inserted successfully!")

    insert_to_db(merged)
    print("DONE: CSV + DB synced")


if __name__ == "__main__":
    main()
