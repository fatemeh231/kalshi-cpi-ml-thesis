# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:06:08 2026
@author: seyedeh fatemeh hosseininasab
Check that the environment is ready.
"""
import sys
import os
import pandas as pd
import numpy as np
import requests
import matplotlib
import scipy
import statsmodels
import tqdm

print("Python:", sys.version.split()[0])
print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("requests:", requests.__version__)
print("matplotlib:", matplotlib.__version__)
print("scipy:", scipy.__version__)
print("statsmodels:", statsmodels.__version__)
print("tqdm:", tqdm.__version__)

print("\nWorking directory:", os.getcwd())
print("Folders here:", os.listdir("."))

# Verify the API is reachable
BASE = "https://api.elections.kalshi.com/trade-api/v2"
r = requests.get(f"{BASE}/markets",
                 params={"series_ticker": "KXCPIYOY", "status": "settled", "limit": 1},
                 timeout=20)
print("\nKalshi API status:", r.status_code)

if r.status_code == 200:
    print("ALL GOOD — proceed to 01_pull_markets.py")
else:
    print("PROBLEM — API returned", r.status_code)