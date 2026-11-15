# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:01:57 2026

@author: seyedeh fatemeh hosseininasab
"""

import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

try:
    r = requests.get(
        f"{BASE}/markets",
        params={"series_ticker": "KXCPIYOY", "status": "settled", "limit": 5},
        timeout=20
    )
    print("Status code:", r.status_code)
    print("Response (first 300 chars):", r.text[:300])
except Exception as e:
    print("REQUEST FAILED —", type(e).__name__, "—", e)