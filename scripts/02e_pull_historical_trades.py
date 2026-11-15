# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:53:38 2026
@author: seyedeh fatemeh hosseininasab
Pull all historical trades for KXCPIYOY markets.
Strategy:
  1. Try series-level pull first (fast): /historical/trades?series_ticker=KXCPIYOY&limit=1000
  2. Paginate with cursor
  3. If series-level yields < 100 trades, fall back to per-ticker loop
Saves: data/raw/kxcpiyoy_trades.csv
"""
import os, time, requests, pandas as pd
from tqdm import tqdm

if not os.path.exists("data/raw"):
    print("ERROR: 'data/raw' not found. Set working directory to 'fomc_codes'.")
    raise SystemExit(1)

BASE = "https://api.elections.kalshi.com/trade-api/v2"
df_m = pd.read_csv("data/raw/kxcpiyoy_markets.csv")
tickers = df_m["ticker"].tolist()

print(f"Pulling trades for {len(tickers)} specific CPI markets...")

all_trades = []
errors = []

for ticker in tqdm(tickers, desc="Pulling"):
    cursor = None
    while True:
        params = {"ticker": ticker, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{BASE}/historical/trades", params=params, timeout=30)
        except Exception as e:
            errors.append((ticker, str(e)))
            break
            
        if r.status_code != 200:
            break
            
        data = r.json()
        batch = data.get("trades", [])
        all_trades.extend(batch)
        
        cursor = data.get("cursor")
        if not cursor or len(batch) == 0:
            break
        time.sleep(0.1)
    time.sleep(0.1)

df_t = pd.DataFrame(all_trades)
if len(df_t) == 0:
    print("\nPROBLEM: zero trades. Stopping.")
    raise SystemExit(1)

print(f"\nTotal trades pulled: {len(df_t)}")
print(f"Tickers with trades: {df_t['ticker'].nunique()} of {len(tickers)}")

# Clean
df_t = df_t.drop_duplicates(subset="trade_id").reset_index(drop=True)
df_t["yes_price_dollars"] = pd.to_numeric(df_t["yes_price_dollars"], errors="coerce")

# FIX: Added format='ISO8601' to handle mixed timestamp formats
df_t["created_time"] = pd.to_datetime(df_t["created_time"], format="ISO8601", utc=True)

print("\n=== SUMMARY ===")
print(f"Date range: {df_t['created_time'].min()} to {df_t['created_time'].max()}")
print("\nTrades per year:")
print(df_t["created_time"].dt.year.value_counts().sort_index())

df_t.to_csv("data/raw/kxcpiyoy_trades.csv", index=False)
print(f"\nSaved: data/raw/kxcpiyoy_trades.csv")
print("NEXT: run 03e_clean_and_h1_v3.py")