# Calibration-Adjusted Machine Learning in Kalshi Macro Prediction Markets

**Author:** Seyedeh Fatemeh Hosseininasab 
**Thesis:** Undergraduate Thesis in Computer Science 
**Institution:** Science and Culture 

## 📌 Project Overview
This repository contains the data pipeline, replication code, and machine learning models for my thesis. The research tests whether Kalshi prediction markets are uniformly efficient by examining calibration quality across FOMC rate-decision and CPI contracts. 

The project makes three contributions:
1. **Replication:** Confirms that Kalshi is near-perfectly calibrated for FOMC decisions but systematically biased for CPI surprises, with bias concentrated in specific price ranges (0.10–0.30 and 0.30–0.70).
2. **Predictive ML:** Introduces a calibration-adjusted ML framework incorporating price-bucket corrections and horizon effects to forecast CPI surprises.
3. **Economic Backtest:** Tests whether the predictive edge survives bid-ask spreads and Kalshi fees in a walk-forward backtest.

## 📊 Current Status
- [x] **H1 (Replication) - PASSED**: Successfully replicated the calibration bias using 223,294 historical trades across 524 markets. 
  - *My Data:* Overall Brier = 0.0602, Bias = -0.0263.
  - *Paper (Calibration & Forecast Accuracy):* Brier = 0.0840, Bias = -0.0895.
- [ ] **H2 (Predictive ML)**: Training Gradient Boosting & Logistic Regression models.
- [ ] **H3 (Economic Backtest)**: Walk-forward backtest with transaction costs.

## 📂 Repository Structure
- `data/` — Data folder (`raw/` is ignored due to size; `processed/` contains the final H1 observation panel).
- `scripts/` — Python scripts for data extraction, cleaning, and modeling.
  - `01b_pull_historical.py`: Pulls historical settled markets.
  - `02e_pull_historical_trades.py`: Pulls trade-level data per ticker.
  - `03e_clean_and_h1_v3.py`: Aggregates to daily last-trades, computes H1 calibration metrics.
- `results/` — Generated plots and summary tables.

## ⚙️ Data Pipeline Notes
- **Kalshi API**: Uses the `/historical/markets` and `/historical/trades` endpoints. 
- **Data Cleaning**: Prices are aggregated to daily last-trades. We forward-fill missing days but *never backward-fill* to prevent look-ahead bias.
- **Geo-blocks**: API calls were executed from a Turkish VPS to bypass geo-blocking.

## 🚀 Setup & Requirements
To run the scripts, install the dependencies:
```bash
pip install -r requirements.txt