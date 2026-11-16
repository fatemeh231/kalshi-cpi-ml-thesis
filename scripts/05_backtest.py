# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 17:10:20 2026
@author: seyedeh fatemeh hosseininasab
H3: Walk-Forward Trading Backtest
Simulates trading on the 2025-2026 test set using ML model predictions.
Applies a 2-cent transaction cost to simulate bid-ask spreads and fees.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

os.makedirs("results", exist_ok=True)

# 1. Load the test predictions saved from H2
df = pd.read_csv("data/processed/h2_test_predictions.csv")
df["date"] = pd.to_datetime(df["date"], format="ISO8601", utc=True)
df = df.sort_values("date")

# 2. Set Trading Parameters
EDGE_THRESHOLD = 0.05   # Only trade if ML and Market differ by at least 5 cents
TRANSACTION_COST = 0.02 # 2 cents per trade (bid-ask spread + fees)
POSITION_SIZE = 1.0     # Trade 1 contract per signal

print(f"Total test observations: {len(df)}")
print(f"Edge Threshold: {EDGE_THRESHOLD*100} cents")
print(f"Transaction Cost: {TRANSACTION_COST*100} cents\n")

# 3. Generate Signals
# If ML > Market + Threshold -> BUY YES
# If ML < Market - Threshold -> BUY NO
df["edge"] = df["ml_prob"] - df["market_price"]
df["trade_signal"] = 0 # 0 = no trade, 1 = buy yes, -1 = buy no

df.loc[df["edge"] > EDGE_THRESHOLD, "trade_signal"] = 1
df.loc[df["edge"] < -EDGE_THRESHOLD, "trade_signal"] = -1

# 4. Calculate PnL
# Payout for YES = settlement (1 or 0). Payout for NO = 1 - settlement
# Cost for YES = market_price + transaction_cost. Cost for NO = (1 - market_price) + transaction_cost

def calculate_pnl(row):
    if row["trade_signal"] == 1:
        # Buy YES
        cost = row["market_price"] + TRANSACTION_COST
        payout = row["settlement"] * 1.0
        return (payout - cost) * POSITION_SIZE
    elif row["trade_signal"] == -1:
        # Buy NO
        cost = (1.0 - row["market_price"]) + TRANSACTION_COST
        payout = (1.0 - row["settlement"]) * 1.0
        return (payout - cost) * POSITION_SIZE
    else:
        return 0.0

df["pnl"] = df.apply(calculate_pnl, axis=1)

# 5. Analyze Results
trades = df[df["trade_signal"] != 0].copy()

if len(trades) == 0:
    print("No trades were generated. The ML model agreed with the market too often.")
    raise SystemExit(0)

total_pnl = trades["pnl"].sum()
win_rate = (trades["pnl"] > 0).mean()
avg_pnl = trades["pnl"].mean()

print("=== BACKTEST RESULTS (2025-2026) ===")
print(f"Total Trades Executed: {len(trades)}")
print(f"Win Rate:              {win_rate*100:.2f}%")
print(f"Total PnL:             ${total_pnl:.2f} per contract")
print(f"Average PnL per Trade: ${avg_pnl:.4f}")

# Sharpe Ratio (Annualized approximation based on daily PnL)
trades["date_only"] = trades["date"].dt.date
daily_pnl = trades.groupby("date_only")["pnl"].sum()
if len(daily_pnl) > 1 and daily_pnl.std() > 0:
    sharpe = (daily_pnl.mean() / daily_pnl.std()) * np.sqrt(252)
    print(f"Approximate Sharpe:    {sharpe:.2f}")
else:
    print("Sharpe Ratio:          N/A (Not enough distinct days)")

# 6. Plot Cumulative PnL
trades = trades.sort_values("date")
trades["cumulative_pnl"] = trades["pnl"].cumsum()

plt.figure(figsize=(10, 6))
plt.plot(trades["date"], trades["cumulative_pnl"], marker="o", linestyle="-", color="green")
plt.axhline(0, color="red", linestyle="--")
plt.title("Cumulative PnL of ML Trading Strategy (2025-2026)")
plt.xlabel("Date")
plt.ylabel("Cumulative PnL ($ per contract)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("results/h3_cumulative_pnl.png", dpi=150)
print("\nSaved plot: results/h3_cumulative_pnl.png")

# 7. Save trade log
trades[["date", "ticker", "market_price", "ml_prob", "trade_signal", "settlement", "pnl"]].to_csv(
    "results/h3_trade_log.csv", index=False
)
print("Saved trade log: results/h3_trade_log.csv")
print("\n=== DONE ===")