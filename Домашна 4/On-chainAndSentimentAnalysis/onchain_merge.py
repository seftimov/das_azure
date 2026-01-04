import pandas as pd
from pathlib import Path
from tqdm import tqdm

PROCESSED_DIR = Path("coinmetrics_processed")
OUTPUT_DIR = Path("merged_data")
OUTPUT_DIR.mkdir(exist_ok=True)

print("Finding all CSV files...")
csv_files = sorted(list(PROCESSED_DIR.glob("*.csv")))

if not csv_files:
    print("No CSV files found!")
    exit(1)

print(f"Found {len(csv_files)} files")

master_df = pd.DataFrame()
total_rows = 0

print("\nMerging files one by one...")
for csv_path in tqdm(csv_files, desc="Merging"):
    symbol = csv_path.stem.split('_')[0].upper()

    try:
        df = pd.read_csv(csv_path)
        df['symbol'] = symbol
        master_df = pd.concat([master_df, df], ignore_index=True)
        total_rows += len(df)
        print(f"   {csv_path.name} → {symbol}: {len(df):,} rows (total: {total_rows:,})")
    except Exception as e:
        print(f"Error: {csv_path.name} - {e}")

print(f"\nMaster merge complete!")
print(f"Total rows: {len(master_df):,}")
print(f"Coins: {master_df['symbol'].nunique()}")

output_path = OUTPUT_DIR / "master_onchain_merged.csv"
master_df.to_csv(output_path, index=False)

print(f"\nSaved: {output_path.absolute()}")
print(f"Columns: {list(master_df.columns)}")

print("\nPreview (first 3 rows):")
print(master_df[['symbol', 'time', 'AdrActCnt', 'NVT_Ratio']].head(3).to_string(index=False))
