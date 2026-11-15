"""
Pull ALL historical settled KXCPIYOY markets from Kalshi.
Uses /historical/markets with pagination (the only endpoint that
has data older than ~3 months per Rise paper p.59).
Saves to data/raw/kxcpiyoy_markets.csv
"""
import os
import time
import requests
import pandas as pd

BASE = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = "KXCPIYOY"

os.makedirs("data/raw", exist_ok=True)

all_markets = []
cursor = None
page = 0

while True:
    page += 1
    params = {"series_ticker": SERIES, "limit": 200}
    if cursor:
        params["cursor"] = cursor

    r = requests.get(f"{BASE}/historical/markets", params=params, timeout=30)
    if r.status_code != 200:
        print(f"ERROR page {page}: status {r.status_code}")
        print(r.text[:300])
        break

    data = r.json()
    batch = data.get("markets", [])
    all_markets.extend(batch)
    print(f"Page {page}: +{len(batch)} markets (total {len(all_markets)})")

    cursor = data.get("cursor")
    if not cursor or len(batch) == 0:
        break
    time.sleep(0.2)

if not all_markets:
    print("PROBLEM: zero markets. Stopping.")
    raise SystemExit(1)

df = pd.DataFrame(all_markets)
df = df.drop_duplicates(subset="ticker").reset_index(drop=True)

# Derive series_ticker if missing
if "series_ticker" not in df.columns:
    df["series_ticker"] = df["event_ticker"].str.split("-").str[0]

print("\n=== SUMMARY ===")
print(f"Total markets: {len(df)}")
print(f"Unique events: {df['event_ticker'].nunique()}")
print(f"Events:        {sorted(df['event_ticker'].unique().tolist())}")
print(f"Date range:    {df['close_time'].min()}  to  {df['close_time'].max()}")
print(f"Result counts: {df['result'].value_counts(dropna=False).to_dict()}")
print(f"Floor strike range: {df['floor_strike'].min()}  to  {df['floor_strike'].max()}")

out = "data/raw/kxcpiyoy_markets.csv"
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
print("NEXT: run 02b_pull_prices.py")