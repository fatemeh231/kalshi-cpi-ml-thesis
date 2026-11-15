# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:16:11 2026

@author: seyedeh fatemeh hosseininasab
Pull daily price history (last trade + volume) for each market.
Uses price.close_dollars (new format); leaves NaN when no trade.
Carry-forward happens later in 03_clean.
Saves to data/raw/kxcpiyoy_prices.csv
"""
import os
import time
import datetime as dt
import requests
import pandas as pd
from tqdm import tqdm

BASE = "https://api.elections.kalshi.com/trade-api/v2"

df_m = pd.read_csv("data/raw/kxcpiyoy_markets.csv")
print(f"Loaded {len(df_m)} markets")

if "series_ticker" not in df_m.columns:
    df_m["series_ticker"] = df_m["event_ticker"].str.split("-").str[0]

prices = []
errors = []
live_ok, hist_ok, both_fail = 0, 0, 0

for _, row in tqdm(df_m.iterrows(), total=len(df_m), desc="Pulling"):
    ticker = row["ticker"]
    series = row["series_ticker"]

    try:
        open_ts = int(dt.datetime.fromisoformat(
            row["open_time"].replace("Z", "+00:00")).timestamp())
        close_ts = int(dt.datetime.fromisoformat(
            row["close_time"].replace("Z", "+00:00")).timestamp())
    except Exception as e:
        errors.append((ticker, f"time: {e}"))
        both_fail += 1
        continue

    params = {
        "start_ts": open_ts,
        "end_ts": close_ts,
        "period_interval": 1440,
    }

    # --- Tier 1: live endpoint ---
    url_live = f"{BASE}/series/{series}/markets/{ticker}/candlesticks"
    try:
        cr = requests.get(url_live, params=params, timeout=30)
    except Exception as e:
        errors.append((ticker, f"live exception: {e}"))
        both_fail += 1
        time.sleep(0.3)
        continue

    data = None
    tier = None

    if cr.status_code == 200:
        data = cr.json()
        tier = "live"
        live_ok += 1
    elif cr.status_code == 404:
        # --- Tier 2: historical endpoint ---
        url_hist = f"{BASE}/historical/markets/{ticker}/candlesticks"
        try:
            cr2 = requests.get(url_hist, params=params, timeout=30)
            if cr2.status_code == 200:
                data = cr2.json()
                tier = "historical"
                hist_ok += 1
            else:
                errors.append((ticker, f"hist {cr2.status_code}"))
                both_fail += 1
        except Exception as e:
            errors.append((ticker, f"hist exception: {e}"))
            both_fail += 1
    else:
        # Any other error on live (400, 500) — try historical as last resort
        url_hist = f"{BASE}/historical/markets/{ticker}/candlesticks"
        try:
            cr2 = requests.get(url_hist, params=params, timeout=30)
            if cr2.status_code == 200:
                data = cr2.json()
                tier = "historical"
                hist_ok += 1
            else:
                errors.append((ticker, f"live {cr.status_code}, hist {cr2.status_code}"))
                both_fail += 1
        except Exception as e:
            errors.append((ticker, f"live {cr.status_code}, hist exception: {e}"))
            both_fail += 1

    if data:
        for c in data.get("candlesticks", []):
            ts = pd.to_datetime(c["end_period_ts"], unit="s", utc=True)

            price_val = None
            if c.get("price"):
                p = c["price"]
                if p.get("close_dollars") is not None:
                    price_val = float(p["close_dollars"])
                elif p.get("close") is not None:
                    price_val = float(p["close"]) / 100.0

            prices.append({
                "ticker": ticker,
                "ts": ts,
                "close": price_val,
                "volume": float(c.get("volume_fp", 0) or 0),
                "tier": tier,
            })

    time.sleep(0.2)

df_p = pd.DataFrame(prices)

print(f"\n=== SUMMARY ===")
print(f"Markets attempted: {len(df_m)}")
print(f"  Live endpoint OK:       {live_ok}")
print(f"  Historical endpoint OK: {hist_ok}")
print(f"  Both failed:            {both_fail}")
print(f"\nTotal price rows:  {len(df_p)}")
print(f"With trades:       {df_p['close'].notna().sum()}")
print(f"Without trades:    {df_p['close'].isna().sum()}")
print(f"Errors:            {len(errors)}")
if errors:
    print("\nFirst 10 errors:")
    for t, e in errors[:10]:
        print(f"  {t}: {e}")

df_p.to_csv("data/raw/kxcpiyoy_prices.csv", index=False)
print(f"\nSaved: data/raw/kxcpiyoy_prices.csv")
print("NEXT: run 03_clean_and_h1.py")