# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:26:08 2026

@author: seyedeh fatemeh hosseininasab
Find the correct endpoint for historical candlestick data.
Tests 8 candidate paths on one known-failing ticker.
"""
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# A ticker that FAILED with 404 (from your error log)
failing_ticker = "KXCPIYOY-26JUL-T5.0"
failing_series = "KXCPIYOY"

# A known-OLD ticker to test
old_ticker = "CPIYOY-22DEC-T2.5"   # older format
old_series = "CPIYOY"

def test(label, url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"\n--- {label} ---")
        print(f"    {r.status_code}  {url}")
        if r.status_code == 200:
            data = r.json()
            keys = list(data.keys())
            print(f"    keys: {keys}")
            for k in ["candlesticks", "trades", "market"]:
                if k in data:
                    v = data[k]
                    n = len(v) if isinstance(v, list) else "(dict)"
                    print(f"    {k}: {n}")
                    if isinstance(v, list) and v:
                        print(f"    first item keys: {list(v[0].keys())[:10]}")
                    return True
        else:
            print(f"    body: {r.text[:200]}")
    except Exception as e:
        print(f"    exception: {e}")
    return False

print("=" * 60)
print("TESTING FAILING TICKER:", failing_ticker)
print("=" * 60)

test("1. standard candlesticks",
     f"{BASE}/series/{failing_series}/markets/{failing_ticker}/candlesticks",
     {"period_interval": 1440})

test("2. historical candlesticks (series in path)",
     f"{BASE}/historical/series/{failing_series}/markets/{failing_ticker}/candlesticks",
     {"period_interval": 1440})

test("3. historical candlesticks (no series in path)",
     f"{BASE}/historical/markets/{failing_ticker}/candlesticks",
     {"period_interval": 1440})

test("4. trades",
     f"{BASE}/markets/{failing_ticker}/trades",
     {"limit": 100})

test("5. historical trades",
     f"{BASE}/historical/markets/{failing_ticker}/trades",
     {"limit": 100})

test("6. market detail (to confirm ticker exists)",
     f"{BASE}/historical/markets/{failing_ticker}")

print("\n" + "=" * 60)
print("TESTING OLD TICKER:", old_ticker)
print("=" * 60)

test("7. old standard candlesticks",
     f"{BASE}/series/{old_series}/markets/{old_ticker}/candlesticks",
     {"period_interval": 1440})

test("8. old historical candlesticks",
     f"{BASE}/historical/series/{old_series}/markets/{old_ticker}/candlesticks",
     {"period_interval": 1440})

print("\n=== DONE ===")
print("Paste the FULL output here.")