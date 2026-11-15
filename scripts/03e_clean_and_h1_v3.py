# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 14:23:04 2026
@author: seyedeh fatemeh hosseininasab
Aggregate trades to daily last-trade per Rise paper p.64.
Compute H1: Brier by horizon, bias by bucket, calibration curve.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

os.makedirs("data/processed", exist_ok=True)
os.makedirs("results", exist_ok=True)

df_t = pd.read_csv("data/raw/kxcpiyoy_trades.csv")
df_m = pd.read_csv("data/raw/kxcpiyoy_markets.csv")
print(f"Trades: {len(df_t)}   Markets: {len(df_m)}")

# FIX: Added format='ISO8601'
df_t["created_time"] = pd.to_datetime(df_t["created_time"], format="ISO8601", utc=True)
df_t["yes_price_dollars"] = pd.to_numeric(df_t["yes_price_dollars"], errors="coerce")
df_t = df_t.dropna(subset=["yes_price_dollars"])

# --- DAILY LAST TRADE (Rise p.64) ---
df_t = df_t.sort_values(["ticker", "created_time"])
df_t["date"] = df_t["created_time"].dt.normalize()
daily = df_t.groupby(["ticker", "date"]).agg(
    close=("yes_price_dollars", "last"),
    n_trades=("trade_id", "count"),
).reset_index()
print(f"Daily rows: {len(daily)}   Tickers: {daily['ticker'].nunique()}")

# --- SETTLEMENT ---
df_m["settlement"] = (df_m["result"] == "yes").astype(int)

# --- EXTRACT AT 6 HORIZONS ---
horizons = [30, 14, 7, 3, 1, 1/24]
observations = []

market_info = df_m.set_index("ticker")[["close_time", "settlement"]].to_dict("index")

for ticker, group in daily.groupby("ticker"):
    if ticker not in market_info:
        continue
    info = market_info[ticker]
    # FIX: Added format='ISO8601'
    close_ts = pd.to_datetime(info["close_time"], format="ISO8601", utc=True)
    settlement = info["settlement"]
    group = group.sort_values("date")

    for h in horizons:
        target = close_ts - pd.Timedelta(days=h)
        eligible = group[group["date"] <= target]
        if eligible.empty:
            continue
        row = eligible.iloc[-1]
        observations.append({
            "ticker": ticker,
            "horizon": h,
            "date": row["date"],
            "close": row["close"],
            "settlement": settlement,
        })

df = pd.DataFrame(observations)
print(f"\nHorizon observations: {len(df)}")
print(f"Unique tickers:       {df['ticker'].nunique()}")
print(f"\nHorizon counts:\n{df['horizon'].value_counts().sort_index()}")

# --- BRIER BY HORIZON ---
df["brier"] = (df["close"] - df["settlement"]) ** 2
print("\n=== BRIER BY HORIZON ===")
print(df.groupby("horizon")["brier"].agg(["mean", "count"]).round(4))

# --- BUCKET ANALYSIS ---
bins = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0]
df["bucket"] = pd.cut(df["close"], bins=bins, include_lowest=True, right=False)
print("\n=== BIAS BY PRICE BUCKET ===")
print(df.groupby("bucket", observed=True).apply(
    lambda x: pd.Series({
        "n": len(x),
        "mean_price": round(x["close"].mean(), 3),
        "win_rate": round(x["settlement"].mean(), 3),
        "bias": round(x["settlement"].mean() - x["close"].mean(), 3),
    })
))

# --- OVERALL ---
ob = df["brier"].mean()
oi = (df["settlement"] - df["close"]).mean()
om = (df["close"] - df["settlement"]).abs().mean()
print("\n=== OVERALL ===")
print(f"N obs:   {len(df)}")
print(f"Brier:   {ob:.4f}   (paper: 0.0840)")
print(f"Bias:    {oi:.4f}   (paper: -0.0895)")
print(f"MAE:     {om:.4f}")

# --- SAVE ---
df.to_csv("data/processed/kxcpiyoy_panel_v3.csv", index=False)
pd.DataFrame({
    "metric": ["n_obs", "overall_brier", "overall_bias", "overall_mae"],
    "my_data": [len(df), round(ob, 4), round(oi, 4), round(om, 4)],
    "paper": [561, 0.0840, -0.0895, None],
}).to_csv("results/h1_summary_v3.csv", index=False)

# --- PLOT ---
fig, ax = plt.subplots(figsize=(7, 7))
ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
for bucket, group in df.groupby("bucket", observed=True):
    if len(group) < 5:
        continue
    p, y = group["close"].mean(), group["settlement"].mean()
    lo, hi = proportion_confint(int(group["settlement"].sum()), len(group), alpha=0.05)
    ax.errorbar(p, y, yerr=[[y-lo], [hi-y]], fmt="o", capsize=3,
                label=f"{bucket} (n={len(group)})")
ax.set_xlabel("Last trade price"); ax.set_ylabel("Win rate")
ax.set_title("Calibration — KXCPIYOY v3 (from trades)")
ax.legend(fontsize=7); ax.set_xlim(0,1); ax.set_ylim(0,1)
plt.tight_layout()
plt.savefig("results/calibration_kxcpiyoy_v3.png", dpi=150)
plt.close()

print("\nSaved: data/processed/kxcpiyoy_panel_v3.csv")
print("Saved: results/h1_summary_v3.csv")
print("Saved: results/calibration_kxcpiyoy_v3.png")
print("\n=== DONE ===")