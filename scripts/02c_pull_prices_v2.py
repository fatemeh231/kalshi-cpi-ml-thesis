# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:41:53 2026
@author: seyedeh fatemeh hosseininasab
Pull daily candles with last trade + bid/ask.
Saves richer data so 03c can reconstruct a good price series.
"""
import os, time, datetime as dt
import requests, pandas as pd
from tqdm import tqdm

BASE = "https://api.elections.kalshi.com/trade-api/v2"

df_m = pd.read_csv("data/raw/kxcpiyoy_markets.csv")
print(f"Loaded {len(df_m)} markets")
if "series_ticker" not in df_m.columns:
    df_m["series_ticker"] = df_m["event_ticker"].str.split("-").str[0]

rows = []
errors = []

for _, row in tqdm(df_m.iterrows(), total=len(df_m), desc="Pulling"):
    ticker = row["ticker"]
    series = row["series_ticker"]

    try:
        open_ts  = int(dt.datetime.fromisoformat(row["open_time"].replace("Z", "+00:00")).timestamp())
        close_ts = int(dt.datetime.fromisoformat(row["close_time"].replace("Z", "+00:00")).timestamp())
    except Exception as e:
        errors.append((ticker, f"time: {e}")); continue

    params = {"start_ts": open_ts, "end_ts": close_ts, "period_interval": 1440}
    data = None

    for url in [
        f"{BASE}/series/{series}/markets/{ticker}/candlesticks",
        f"{BASE}/historical/markets/{ticker}/candlesticks",
    ]:
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 200:
                data = r.json(); break
        except Exception:
            pass

    if data is None:
        errors.append((ticker, "both endpoints failed")); continue

    for c in data.get("candlesticks", []):
        ts = pd.to_datetime(c["end_period_ts"], unit="s", utc=True)

        last_price = None
        if c.get("price") and c["price"].get("close_dollars") is not None:
            last_price = float(c["price"]["close_dollars"])

        try:    bid = float(c["yes_bid"]["close_dollars"])
        except (KeyError, TypeError, ValueError): bid = None
        try:    ask = float(c["yes_ask"]["close_dollars"])
        except (KeyError, TypeError, ValueError): ask = None

        spread = (ask - bid) if (bid is not None and ask is not None) else None

        rows.append({
            "ticker": ticker, "ts": ts,
            "last_price": last_price,
            "bid": bid, "ask": ask, "spread": spread,
        })
    time.sleep(0.2)

df = pd.DataFrame(rows)
print(f"\nRows: {len(df)}  Errors: {len(errors)}")
print(f"Has last trade: {(df['last_price'].notna()).sum()}")
print(f"Has tight spread (<0.10): {((df['spread'].notna()) & (df['spread'] < 0.10)).sum()}")
print(f"Has wide spread (>=0.10): {((df['spread'].notna()) & (df['spread'] >= 0.10)).sum()}")
print(f"Missing bid/ask entirely:  {df['spread'].isna().sum()}")

df.to_csv("data/raw/kxcpiyoy_prices_v2.csv", index=False)
print("\nSaved: data/raw/kxcpiyoy_prices_v2.csv")
print("NEXT: run 03c_clean_and_h1_v2.py")