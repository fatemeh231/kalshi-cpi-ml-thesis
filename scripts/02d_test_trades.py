# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:51:58 2026
@author: seyedeh fatemeh hosseininasab
Test whether trade-level data is available for historical markets.
If yes, we rebuild the pipeline around trades (Rise paper p.59-62).
"""
import requests
import pandas as pd

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# One ticker from each era (from your 650-market CSV)
test_tickers = [
    "CPIYOY-22DEC-T2.5",          # old format, 2022
    "CPIYOY-23JUN-T3.0",          # old format, 2023
    "KXCPIYOY-24NOV-T2.8",        # new format, 2024
    "KXCPIYOY-25JUN-T2.9",        # 2025
    "KXCPIYOY-26JUL-T5.0",        # 2026 (recent)
]

def test(label, url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"\n--- {label} ---")
        print(f"    status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"    keys: {list(data.keys())}")
            if "trades" in data:
                trades = data["trades"]
                print(f"    trades: {len(trades)}")
                if trades:
                    print(f"    first trade: {trades[0]}")
                    return len(trades)
            if "cursor" in data:
                print(f"    cursor: {data['cursor'][:40]}...")
        else:
            print(f"    body: {r.text[:200]}")
    except Exception as e:
        print(f"    exception: {e}")
    return 0

# Test 1: /historical/markets/{ticker}/trades
for t in test_tickers:
    test(
        f"1. historical/markets/{t}/trades",
        f"{BASE}/historical/markets/{t}/trades",
        {"limit": 100}
    )

# Test 2: /historical/trades (top-level, filter by ticker)
for t in test_tickers[:2]:
    test(
        f"2. historical/trades?ticker={t}",
        f"{BASE}/historical/trades",
        {"ticker": t, "limit": 100}
    )

# Test 3: /markets/{ticker}/trades (live path, might work for old)
for t in test_tickers[:2]:
    test(
        f"3. markets/{t}/trades",
        f"{BASE}/markets/{t}/trades",
        {"limit": 100}
    )