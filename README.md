# Calibration-Adjusted Machine Learning in Kalshi Macro Prediction Markets

**Author:** Seyedeh Fatemeh Hosseininasab
**Thesis:** Undergraduate Thesis in Computer Science
**Institution:** Science and Culture University

## 📌 Project Overview
This repository contains the data pipeline, replication code, machine learning models, and trading backtest for my thesis. The research tests whether Kalshi prediction markets are uniformly efficient by examining calibration quality across FOMC rate-decision and CPI contracts. 

The project makes three contributions:
1. **Replication:** Confirms that Kalshi is near-perfectly calibrated for FOMC decisions but systematically biased for CPI surprises, with bias concentrated in specific price ranges.
2. **Predictive ML:** Introduces a calibration-adjusted ML framework incorporating price-bucket corrections and horizon effects to forecast CPI surprises.
3. **Economic Backtest:** Tests whether the predictive edge survives bid-ask spreads and Kalshi fees in a walk-forward backtest.

## 📊 Final Results (All Hypotheses Passed)
- **H1 (Replication) - PASSED:** Successfully replicated the calibration bias using 223,294 historical trades across 524 markets.
  - *My Data:* Overall Brier = 0.0602, Bias = -0.0263.
  - *Benchmark:* Brier = 0.0840, Bias = -0.0895.
- **H2 (Predictive ML) - PASSED:** Trained Logistic Regression and Gradient Boosting models. The ML framework successfully corrected the mid-range pricing bias (0.1–0.5) that the market fails to capture.
- **H3 (Economic Backtest) - PASSED:** Walk-forward backtest with a 2-cent transaction cost model.
  - *Total Trades:* 314
  - *Win Rate:* 75.48%
  - *Total PnL:* +$3.68 per contract
  - *Sharpe Ratio:* 0.71

## 📂 Repository Structure
- `data/` — Data folder (`raw/` is ignored due to size; `processed/` contains the final observation panels).
- `scripts/` — Python scripts for data extraction, cleaning, modeling, and backtesting.
  - `01b_pull_historical.py`: Pulls historical settled markets.
  - `02e_pull_historical_trades.py`: Pulls trade-level data per ticker.
  - `03e_clean_and_h1_v3.py`: Aggregates to daily last-trades, computes H1 metrics.
  - `04b_ml_model_v2.py`: Trains ML models and applies Platt scaling.
  - `05_backtest.py`: Walk-forward trading simulation with fees.
- `results/` — Generated plots, summary tables, and the trading log.

## ⚙️ Data Pipeline Notes
- **Kalshi API:** Uses the `/historical/markets` and `/historical/trades` endpoints.
- **Data Cleaning:** Prices are aggregated to daily last-trades. We forward-fill missing days but *never backward-fill* to prevent look-ahead bias.
- **Geo-blocks:** API calls were executed from a foreign VPS to bypass geo-blocking.

## 🚀 Setup & Requirements
To run the scripts, install the dependencies:
```bash
pip install -r requirements.txt
