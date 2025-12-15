import pandas as pd
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Folders
RAW_DIR = Path("cryptonews_raw")  # where news_expanded_filtered.csv is
NEWS_DIR = Path("nlp")  # where NLP outputs will go
NEWS_DIR.mkdir(exist_ok=True)

# 1) Load expanded + filtered news from cryptonews_raw
INPUT_PATH = RAW_DIR / "news_expanded_filtered.csv"
df = pd.read_csv(INPUT_PATH)
print("Loaded rows:", len(df))
print("Columns:", df.columns.tolist())

# 2) Prepare text field for NLP
df["title"] = df["title"].fillna("")
df["description"] = df["description"].fillna("")
df["text"] = (df["title"] + " " + df["description"]).str.strip()

# 3) Apply VADER sentiment
analyzer = SentimentIntensityAnalyzer()


def compute_vader(text: str) -> float:
    scores = analyzer.polarity_scores(str(text))
    return scores["compound"]


print("Computing VADER sentiment...")
df["vader_score"] = df["text"].apply(compute_vader)

# 4) Normalize date
df["date"] = pd.to_datetime(df["newsDatetime"]).dt.date

# 5) Save per-news sentiment (in nlp folder)
PER_NEWS_PATH = NEWS_DIR / "news_with_vader.csv"
df.to_csv(PER_NEWS_PATH, index=False)
print("Per-news sentiment saved to:", PER_NEWS_PATH)

# 6) Aggregate to daily sentiment per coin
daily = (
    df.groupby(["symbol", "date"])["vader_score"]
    .mean()
    .reset_index()
    .rename(columns={"vader_score": "sentiment_score"})
)

DAILY_PATH = NEWS_DIR / "daily_sentiment_per_coin.csv"
daily.to_csv(DAILY_PATH, index=False)
print("Daily sentiment saved to:", DAILY_PATH)

print("\nPreview (daily sentiment):")
print(daily.head(10))
