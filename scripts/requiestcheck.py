# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:00:36 2026

@author: seyedeh fatemeh hosseininasab
"""

import requests

try:
    r = requests.get("https://www.google.com", timeout=10)
    print("Internet: OK, status", r.status_code)
except Exception as e:
    print("Internet: FAILED —", e)