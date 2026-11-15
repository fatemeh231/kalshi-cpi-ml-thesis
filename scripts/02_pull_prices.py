# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:10:22 2026
@author: seyedeh fatemeh hosseininasab
Pull daily price history for each market from 01.
Saves to data/raw/kxcpiyoy_prices.csv
Runtime: ~0.2 sec per market. If you have 100 markets, ~30 sec.
         If you have 500 markets, ~3 min.
"""
import os
import time
import datetime as dt
import requests
import pandas as pd
from tqdm import tqdm

BASE = "https://api.elections.kalshi.com/trade-api/v2"

markets_path = "data/raw/kxcpiyoy_markets.csv"
if not os.path.exists(markets_path):
    print(f"ERROR: {markets_path} not found. Run 01_pull_markets.py first.")
    raise SystemExit(1)

df_m = pd.read_csv(markets_path)
print(f"Loaded {len(df_m)} markets")

prices = []
errors = []

for _, row in tqdm(df_m.iterrows(), total=len(df_m), desc="Pulling"):
    ticker = row["ticker"]
    series = row["series_ticker"]

    try:
        open_ts = int(dt.datetime.fromisoformat(
            row["open_time"].replace("Z", "+00:00")).timestamp())
        close_ts = int(dt.datetime.fromisoformat(
            row["close_time"].replace("Z", "+00:00")).timestamp())
    except Exception as e:
        errors.append((ticker, f"time parse: {e}"))
        continue

    url = f"{BASE}/series/{series}/markets/{ticker}/candlesticks"
    params = {
        "start_ts": open_ts,
        "end_ts": close_ts,
        "period_interval": 1440,
    }

    try:
        cr = requests.get(url, params=params, timeout=30)
        if cr.status_code != 200:
            errors.append((ticker, f"status {cr.status_code}"))
            time.sleep(0.5)
            continue

        candles = cr.json().get("candlesticks", [])
        for c in candles:
            prices.append({
                "ticker": ticker,
                "ts": pd.to_datetime(c["end_period_ts"], unit="s", utc=True),
                "close": c["price"]["close"] / 100.0,
            })
    except Exception as e:
        errors.append((ticker, str(e)))

    time.sleep(0.2)

df_p = pd.DataFrame(prices)
print(f"\n=== SUMMARY ===")
print(f"Price rows: {len(df_p)}")
print(f"Errors:     {len(errors)}")
if errors:
    print("First 5 errors:")
    for t, e in errors[:5]:
        print(f"  {t}: {e}")

if len(df_p) == 0:
    print("\nPROBLEM: zero price rows. Stopping.")
    raise SystemExit(1)

out = "data/raw/kxcpiyoy_prices.csv"
df_p.to_csv(out, index=False)
print(f"\nSaved: {out}")
print("NEXT: run 03_clean_and_h1.py")