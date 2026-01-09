import pandas as pd
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "Test123!"
DB_NAME = "crypto_data"

RAW_DIR = Path("cryptonews_raw")
NEWS_DIR = Path("nlp")
NEWS_DIR.mkdir(exist_ok=True)

INPUT_PATH = RAW_DIR / "news_expanded_filtered.csv"


def main():
    df = pd.read_csv(INPUT_PATH)
    print("Loaded rows:", len(df))
    print("Columns:", df.columns.tolist())

    df["title"] = df["title"].fillna("")
    df["description"] = df["description"].fillna("")
    df["text"] = (df["title"] + " " + df["description"]).str.strip()

    analyzer = SentimentIntensityAnalyzer()

    def compute_vader(text: str) -> float:
        return analyzer.polarity_scores(str(text))["compound"]

    print("Computing VADER sentiment...")
    df["vader_score"] = df["text"].apply(compute_vader)

    df["newsDatetime"] = pd.to_datetime(df["newsDatetime"], errors="coerce").dt.tz_localize(None)
    df["date"] = df["newsDatetime"].dt.date

    if "url" not in df.columns:
        df["url"] = ""
    if "sourceUrl" in df.columns:
        df["url"] = df["url"].fillna(df["sourceUrl"])
    df["url"] = df["url"].fillna("").astype(str)

    if "sourceDomain" not in df.columns:
        df["sourceDomain"] = None

    if "currencies" not in df.columns:
        df["currencies"] = None
    df["currencies"] = df["currencies"].fillna("").astype(str)

    if "sourceId" not in df.columns:
        df["sourceId"] = None

    PER_NEWS_PATH = NEWS_DIR / "news_with_vader.csv"
    df.to_csv(PER_NEWS_PATH, index=False)
    print("Per-news sentiment saved:", PER_NEWS_PATH)

    daily = (
        df.groupby(["symbol", "date"])["vader_score"]
        .mean()
        .reset_index()
        .rename(columns={"vader_score": "sentiment_score"})
    )

    DAILY_PATH = NEWS_DIR / "daily_sentiment_per_coin.csv"
    daily.to_csv(DAILY_PATH, index=False)
    print("Daily sentiment saved:", DAILY_PATH)

    print("\nDaily sentiment preview:")
    print(daily.head())

    def insert_news_and_sentiment(df_news, df_daily):
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            autocommit=True
        )
        cursor = conn.cursor()

        news_sql = """
        INSERT INTO news_test (
            symbol, title, description, text, url,
            source_domain, news_datetime, vader_score,
            currencies, sourceId
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        for row in df_news.itertuples(index=False):
            cursor.execute(news_sql, (
                row.symbol,
                row.title,
                row.description,
                row.text,
                row.url,
                row.sourceDomain,
                row.newsDatetime,
                row.vader_score,
                row.currencies,
                row.sourceId
            ))

        daily_sql = """
        INSERT INTO daily_sentiment_test (symbol, date, sentiment_score)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE sentiment_score=VALUES(sentiment_score)
        """

        for row in df_daily.itertuples(index=False):
            cursor.execute(daily_sql, (
                row.symbol,
                row.date,
                row.sentiment_score
            ))

        cursor.close()
        conn.close()
        print("News & daily sentiment inserted into DB")

    insert_news_and_sentiment(df, daily)


if __name__ == "__main__":
    main()
