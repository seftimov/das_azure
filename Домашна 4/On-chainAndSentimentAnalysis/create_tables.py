import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "Test123!"
DB_NAME = "crypto_data"


def create_tables():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True
    )
    cursor = conn.cursor()

    # Table for raw crypto-related news articles and NLP sentiment output
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        symbol VARCHAR(20),
        title LONGTEXT,
        description LONGTEXT,
        text LONGTEXT,
        url TEXT,
        source_domain VARCHAR(100),
        news_datetime DATETIME,
        vader_score DOUBLE,
        currencies TEXT,
        sourceId VARCHAR(50),
        INDEX idx_symbol_date (symbol, news_datetime)
    )
    """)

    # Aggregated daily sentiment per symbol (derived from news data)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_sentiment (
        symbol VARCHAR(20),
        date DATE,
        sentiment_score DOUBLE,
        PRIMARY KEY (symbol, date)
    )
    """)

    # Main on-chain metrics table enriched with sentiment score
    # One row per (symbol, date)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS onchain_metrics (
        symbol VARCHAR(20) NOT NULL,
        date DATE NOT NULL,

        time DATETIME,

        CapMrktEstUSD DOUBLE,
        ReferenceRate DOUBLE,
        ReferenceRateBTC DOUBLE,
        ReferenceRateETH DOUBLE,
        ReferenceRateEUR DOUBLE,
        ReferenceRateUSD DOUBLE,

        volume_reported_spot_usd_1d DOUBLE,
        NVT_Ratio DOUBLE,

        AdrActCnt BIGINT DEFAULT 0,
        AdrBalCnt BIGINT DEFAULT 0,

        AssetCompletionTime DATETIME,
        AssetEODCompletionTime DATETIME,

        CapMVRVCur DOUBLE,
        CapMrktCurUSD DOUBLE,

        IssTotNtv DOUBLE,
        IssTotUSD DOUBLE,

        PriceBTC DOUBLE,
        PriceUSD DOUBLE,

        ROI1yr DOUBLE,
        ROI30d DOUBLE,

        SplyCur DOUBLE,

        TxCnt BIGINT DEFAULT 0,
        TxTfrCnt BIGINT DEFAULT 0,
        BlkCnt BIGINT DEFAULT 0,

        FeeTotNtv DOUBLE,
        HashRate DOUBLE,

        SplyExpFut10yr DOUBLE,

        FlowInExNtv DOUBLE,
        FlowInExUSD DOUBLE,
        FlowOutExNtv DOUBLE,
        FlowOutExUSD DOUBLE,

        SplyExNtv DOUBLE,
        SplyExUSD DOUBLE,

        sentiment_score DOUBLE,

        PRIMARY KEY (symbol, date),
        INDEX idx_time (time),
        INDEX idx_symbol (symbol),
        INDEX idx_price_usd (symbol, date, PriceUSD)
    )
    """)

    cursor.close()
    conn.close()
    print("All tables created successfully")


if __name__ == "__main__":
    create_tables()
