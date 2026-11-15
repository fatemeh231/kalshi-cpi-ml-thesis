# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 13:50:13 2026
@author: seyedeh fatemeh hosseininasab
Rebuild H1 with better price aggregation:
  1. Use last trade if available.
  2. Else use bid-ask midpoint IF spread < 0.10 (informative).
  3. Else mark as missing.
  4. ffill within ticker only as last resort, then drop rows with no price at all.

Saves:
  data/processed/kxcpiyoy_panel_v2.csv
  results/h1_summary_v2.csv
  results/calibration_kxcpiyoy_v2.png
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

os.makedirs("data/processed", exist_ok=True)
os.makedirs("results", exist_ok=True)

df_m = pd.read_csv("data/raw/kxcpiyoy_markets.csv")
df_p = pd.read_csv("data/raw/kxcpiyoy_prices_v2.csv")
print(f"Markets: {len(df_m)}   Price rows: {len(df_p)}")

# Settlement
df_m["settlement"] = (df_m["result"] == "yes").astype(int)

# ---- PRICE RECONSTRUCTION ----
# Step 1: last trade if available
df_p["price_best"] = df_p["last_price"]

# Step 2: midpoint if tight spread and no last trade
mask_mid = df_p["price_best"].isna() & (df_p["spread"] < 0.10) & df_p["bid"].notna() & df_p["ask"].notna()
df_p.loc[mask_mid, "price_best"] = (df_p.loc[mask_mid, "bid"] + df_p.loc[mask_mid, "ask"]) / 2

print(f"Prices from last trade:   {df_p['last_price'].notna().sum()}")
print(f"Prices from midpoint:     {mask_mid.sum()}")
print(f"Prices still missing:     {df_p['price_best'].isna().sum()}")

# Step 3: ffill within ticker (only for filling gaps)
df_p = df_p.sort_values(["ticker", "ts"])
df_p["price_best"] = df_p.groupby("ticker")["price_best"].ffill()

# Drop rows that still have no price
df_p = df_p.dropna(subset=["price_best"])

# ---- MERGE ----
df = df_p.merge(
    df_m[["ticker", "close_time", "settlement"]],
    on="ticker", how="inner"
)
df["close"] = df["price_best"]
df["ts"] = pd.to_datetime(df["ts"], utc=True)
df["close_time"] = pd.to_datetime(df["close_time"], utc=True)

# ---- TRIM START ----
first_ts = df.groupby("ticker")["ts"].min().rename("first_ts")
df = df.merge(first_ts, on="ticker", how="left")
df = df[df["ts"] >= df["first_ts"]]

# ---- DAYS TO RESOLUTION ----
df["days_to_resolution"] = (df["close_time"] - df["ts"]).dt.total_seconds() / 86400
df = df[(df["days_to_resolution"] >= 0) & (df["days_to_resolution"] <= 45)]
assert (df["days_to_resolution"] >= 0).all()

# ---- HORIZON ----
horizons = [30, 14, 7, 3, 1, 1/24]
df["horizon"] = df["days_to_resolution"].apply(
    lambda d: min(horizons, key=lambda h: abs(d - h))
)

print(f"\nCleaned rows:   {len(df)}")
print(f"Unique markets: {df['ticker'].nunique()}")
event_ids = df['ticker'].str.extract(r'-(\d{2}[A-Z]{3})')[0]
print(f"Unique events:  {event_ids.nunique()}")
print(f"\nHorizon counts:\n{df['horizon'].value_counts().sort_index()}")

# ---- BRIER BY HORIZON ----
df["brier"] = (df["close"] - df["settlement"]) ** 2
print("\n=== BRIER BY HORIZON ===")
print(df.groupby("horizon")["brier"].agg(["mean", "count"]).round(4))

# ---- BUCKET ----
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

# ---- OVERALL ----
ob = df["brier"].mean()
oi = (df["settlement"] - df["close"]).mean()
om = (df["close"] - df["settlement"]).abs().mean()
print("\n=== OVERALL ===")
print(f"N obs:   {len(df)}")
print(f"Brier:   {ob:.4f}   (paper: 0.0840)")
print(f"Bias:    {oi:.4f}   (paper: -0.0895)")
print(f"MAE:     {om:.4f}")

# ---- SAVE ----
df.reset_index(drop=True).to_csv("data/processed/kxcpiyoy_panel_v2.csv", index=False)
pd.DataFrame({
    "metric": ["n_obs", "overall_brier", "overall_bias", "overall_mae"],
    "my_data": [len(df), round(ob, 4), round(oi, 4), round(om, 4)],
    "paper": [561, 0.0840, -0.0895, None],
}).to_csv("results/h1_summary_v2.csv", index=False)

# ---- PLOT ----
fig, ax = plt.subplots(figsize=(7, 7))
ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
for bucket, group in df.groupby("bucket", observed=True):
    if len(group) < 5: continue
    p, y = group["close"].mean(), group["settlement"].mean()
    lo, hi = proportion_confint(int(group["settlement"].sum()), len(group), alpha=0.05)
    ax.errorbar(p, y, yerr=[[y-lo], [hi-y]], fmt="o", capsize=3,
                label=f"{bucket} (n={len(group)})")
ax.set_xlabel("Market price"); ax.set_ylabel("Win rate")
ax.set_title("Calibration — KXCPIYOY v2 (last trade + midpoint)")
ax.legend(fontsize=7); ax.set_xlim(0,1); ax.set_ylim(0,1)
plt.tight_layout()
plt.savefig("results/calibration_kxcpiyoy_v2.png", dpi=150)
plt.close()

print("\nSaved: data/processed/kxcpiyoy_panel_v2.csv")
print("Saved: results/h1_summary_v2.csv")
print("Saved: results/calibration_kxcpiyoy_v2.png")
print("\n=== DONE ===")