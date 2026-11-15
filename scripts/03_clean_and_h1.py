# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:36:26 2026
@author: seyedeh fatemeh hosseininasab
Merge, clean (carry-forward + trim start), compute H1 metrics.
Saves:
  data/processed/kxcpiyoy_panel.csv
  results/h1_summary.csv
  results/calibration_kxcpiyoy.png
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

os.makedirs("data/processed", exist_ok=True)
os.makedirs("results", exist_ok=True)

df_m = pd.read_csv("data/raw/kxcpiyoy_markets.csv")
df_p = pd.read_csv("data/raw/kxcpiyoy_prices.csv")
print(f"Markets: {len(df_m)}   Price rows: {len(df_p)}")

# --- Settlement: prefer result, fall back to settlement_value_dollars ---
if "result" in df_m.columns:
    df_m["settlement"] = (df_m["result"] == "yes").astype(int)
    print(f"Using 'result' column. Counts: {df_m['settlement'].value_counts().to_dict()}")
elif "settlement_value_dollars" in df_m.columns:
    df_m["settlement"] = pd.to_numeric(
        df_m["settlement_value_dollars"], errors="coerce"
    ).fillna(0).astype(int)
    print(f"Using 'settlement_value_dollars'. Counts: {df_m['settlement'].value_counts().to_dict()}")
else:
    raise SystemExit("No settlement column found")

# Cross-check
if "settlement_value_dollars" in df_m.columns and "result" in df_m.columns:
    check = pd.to_numeric(df_m["settlement_value_dollars"], errors="coerce")
    mismatches = ((check == 1) & (df_m["result"] != "yes")).sum() + \
                 ((check == 0) & (df_m["result"] != "no")).sum()
    print(f"Settlement cross-check mismatches: {mismatches} (should be 0)")

# --- Merge ---
df = df_p.merge(
    df_m[["ticker", "close_time", "settlement"]],
    on="ticker", how="inner"
)
print(f"After merge: {len(df)}")

# --- Sort + carry-forward ---
df["ts"] = pd.to_datetime(df["ts"], utc=True)
df["close_time"] = pd.to_datetime(df["close_time"], utc=True)
df = df.sort_values(["ticker", "ts"])
df["close"] = df.groupby("ticker")["close"].ffill()

# --- Trim start ---
first_trade = (
    df.dropna(subset=["close"])
      .groupby("ticker")["ts"].min()
      .rename("first_ts")
)
df = df.merge(first_trade, on="ticker", how="left")
df = df[(df["ts"] >= df["first_ts"]) & df["close"].notna()].copy()
print(f"After trim start: {len(df)}")

# --- Days to resolution ---
df["days_to_resolution"] = (
    (df["close_time"] - df["ts"]).dt.total_seconds() / 86400
)
df = df[(df["days_to_resolution"] >= 0) & (df["days_to_resolution"] <= 45)]
assert (df["days_to_resolution"] >= 0).all(), "LOOK-AHEAD BIAS"
print(f"After date filter (0-45 days): {len(df)}")

# --- Horizon bucket ---
horizons = [30, 14, 7, 3, 1, 1/24]
df["horizon"] = df["days_to_resolution"].apply(
    lambda d: min(horizons, key=lambda h: abs(d - h))
)

# --- Unique event count (FIXED: regex outside f-string) ---
event_ids = df["ticker"].str.extract(r"-(\d{2}[A-Z]{3})")[0]
n_events = event_ids.nunique()

print(f"\nCleaned rows:   {len(df)}")
print(f"Unique markets: {df['ticker'].nunique()}")
print(f"Unique events:  {n_events}")
print(f"\nHorizon counts:\n{df['horizon'].value_counts().sort_index()}")

# --- Brier by horizon ---
df["brier"] = (df["close"] - df["settlement"]) ** 2
print("\n=== BRIER BY HORIZON ===")
print(df.groupby("horizon")["brier"].agg(["mean", "count"]).round(4))

# --- Bias by price bucket ---
bins = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0]
df["bucket"] = pd.cut(df["close"], bins=bins, include_lowest=True, right=False)
print("\n=== BIAS BY PRICE BUCKET ===")
bucket_stats = df.groupby("bucket", observed=True).apply(
    lambda x: pd.Series({
        "n":          len(x),
        "mean_price": round(x["close"].mean(), 3),
        "win_rate":   round(x["settlement"].mean(), 3),
        "bias":       round(x["settlement"].mean() - x["close"].mean(), 3),
    })
)
print(bucket_stats)

# --- Overall ---
overall_brier = df["brier"].mean()
overall_bias  = (df["settlement"] - df["close"]).mean()
overall_mae   = (df["close"] - df["settlement"]).abs().mean()

print("\n=== OVERALL ===")
print(f"N obs:   {len(df)}")
print(f"Brier:   {overall_brier:.4f}   (paper: 0.0840)")
print(f"Bias:    {overall_bias:.4f}   (paper: -0.0895)")
print(f"MAE:     {overall_mae:.4f}")

# --- Save ---
df.reset_index(drop=True).to_csv("data/processed/kxcpiyoy_panel.csv", index=False)
pd.DataFrame({
    "metric": ["n_obs", "overall_brier", "overall_bias", "overall_mae"],
    "my_data": [len(df), round(overall_brier, 4),
                round(overall_bias, 4), round(overall_mae, 4)],
    "paper": [561, 0.0840, -0.0895, None],
}).to_csv("results/h1_summary.csv", index=False)

# --- Calibration plot ---
fig, ax = plt.subplots(figsize=(7, 7))
ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
for bucket, group in df.groupby("bucket", observed=True):
    if len(group) < 5:
        continue
    p, y = group["close"].mean(), group["settlement"].mean()
    lo, hi = proportion_confint(int(group["settlement"].sum()), len(group), alpha=0.05)
    ax.errorbar(p, y, yerr=[[y-lo], [hi-y]], fmt="o", capsize=3,
                label=f"{bucket} (n={len(group)})")
ax.set_xlabel("Market price (implied probability)")
ax.set_ylabel("Win rate")
ax.set_title("Calibration — KXCPIYOY (Dec 2022 – Sep 2026)")
ax.legend(fontsize=7); ax.set_xlim(0,1); ax.set_ylim(0,1)
plt.tight_layout()
plt.savefig("results/calibration_kxcpiyoy.png", dpi=150)
plt.close()

print("\nSaved: data/processed/kxcpiyoy_panel.csv")
print("Saved: results/h1_summary.csv")
print("Saved: results/calibration_kxcpiyoy.png")
print("\n=== DONE ===")