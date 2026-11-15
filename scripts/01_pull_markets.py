# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:08:08 2026
@author: seyedeh fatemeh hosseininasab
Pull all settled KXCPIYOY markets from Kalshi.
Handles pagination. Saves to data/raw/kxcpiyoy_markets.csv

Expected runtime: < 30 seconds.
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
    params = {"series_ticker": SERIES, "status": "settled", "limit": 200}
    if cursor:
        params["cursor"] = cursor

    r = requests.get(f"{BASE}/markets", params=params, timeout=30)
    if r.status_code != 200:
        print(f"ERROR on page {page}: status {r.status_code}")
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
    print("PROBLEM: zero markets pulled. Stopping.")
    raise SystemExit(1)

df = pd.DataFrame(all_markets)
print("\n=== SUMMARY ===")
print("Total markets:", len(df))
print("Columns:", df.columns.tolist())
print("\nResult value counts:")
print(df["result"].value_counts(dropna=False))
print("\nDate range:")
print("  Earliest close_time:", df["close_time"].min())
print("  Latest close_time:",   df["close_time"].max())
print("\nSample tickers:")
print(df["ticker"].head(5).tolist())

out = "data/raw/kxcpiyoy_markets.csv"
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
print("NEXT: run 02_pull_prices.py")
