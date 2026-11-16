# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 17:07:46 2026
@author: seyedeh fatemeh hosseininasab
H2 v2: Improved Feature Engineering & Platt Scaling
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

# 1. Load Data
df = pd.read_csv("data/processed/kxcpiyoy_panel_v3.csv")
df["date"] = pd.to_datetime(df["date"], format="ISO8601", utc=True)
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["market_price"] = df["close"]

# 2. NEW FEATURE ENGINEERING (Targeting the H1 bias)
df["is_low_range"]  = ((df["market_price"] >= 0.10) & (df["market_price"] < 0.30)).astype(int)
df["is_mid_range"]  = ((df["market_price"] >= 0.30) & (df["market_price"] < 0.50)).astype(int)
df["is_high_range"] = ((df["market_price"] >= 0.70) & (df["market_price"] < 0.90)).astype(int)
df["distance_from_05"] = np.abs(df["market_price"] - 0.5)

features = [
    "market_price", "horizon", "month", 
    "is_low_range", "is_mid_range", "is_high_range", "distance_from_05"
]
X = df[features]
y = df["settlement"]

# 3. Train/Test Split
train_mask = df["year"] <= 2024
test_mask  = df["year"] >= 2025

X_train, y_train = X[train_mask], y[train_mask]
X_test, y_test = X[test_mask], y[test_mask]

print(f"Train (2022-2024): {len(X_train)} | Test (2025-2026): {len(X_test)}")

# 4. Baseline
market_brier = brier_score_loss(y_test, X_test["market_price"])
print(f"\n--- BASELINE ---")
print(f"Market Raw Brier Score: {market_brier:.4f}")

# 5. Train Models (Using Platt/Sigmoid calibration)
print("\nTraining models...")

# A. Logistic Regression
lr_pipeline = make_pipeline(StandardScaler(), LogisticRegression(random_state=42, max_iter=1000))
lr_cal = CalibratedClassifierCV(lr_pipeline, method="sigmoid", cv=3)
lr_cal.fit(X_train, y_train)

# B. Random Forest (Better for small tabular data than Gradient Boosting)
rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
rf_cal = CalibratedClassifierCV(rf_model, method="sigmoid", cv=3)
rf_cal.fit(X_train, y_train)

# C. Gradient Boosting (Reduced iterations to prevent overfitting)
gb_model = HistGradientBoostingClassifier(random_state=42, max_iter=50, max_depth=3)
gb_cal = CalibratedClassifierCV(gb_model, method="sigmoid", cv=3)
gb_cal.fit(X_train, y_train)

# 6. Evaluate
lr_probs = lr_cal.predict_proba(X_test)[:, 1]
rf_probs = rf_cal.predict_proba(X_test)[:, 1]
gb_probs = gb_cal.predict_proba(X_test)[:, 1]

lr_brier = brier_score_loss(y_test, lr_probs)
rf_brier = brier_score_loss(y_test, rf_probs)
gb_brier = brier_score_loss(y_test, gb_probs)

print("\n--- ML MODEL RESULTS ---")
print(f"Logistic Regression Brier: {lr_brier:.4f}")
print(f"Random Forest Brier:       {rf_brier:.4f}")
print(f"Gradient Boosting Brier:   {gb_brier:.4f}")

# 7. Verdict
print("\n=== H2 VERDICT ===")
best_brier = min(lr_brier, rf_brier, gb_brier)
if best_brier < market_brier:
    print(f"✅ PASS: ML beats the market! ({best_brier:.4f} < {market_brier:.4f})")
    if best_brier == lr_brier:
        best_probs = lr_probs
        best_name = "Logistic Regression"
    elif best_brier == rf_brier:
        best_probs = rf_probs
        best_name = "Random Forest"
    else:
        best_probs = gb_probs
        best_name = "Gradient Boosting"
    print(f"Winner: {best_name}")
else:
    print(f"❌ FAIL: ML did not beat the market. Best ML: {best_brier:.4f} vs Market: {market_brier:.4f}")
    # We still save the best ML probabilities for H3 (to see if it can trade)
    best_probs = lr_probs if lr_brier == best_brier else (rf_probs if rf_brier == best_brier else gb_probs)
    best_name = "Best ML Attempt"

# 8. Save predictions
df_test = df[test_mask].copy()
df_test["ml_prob"] = best_probs
df_test.to_csv("data/processed/h2_test_predictions.csv", index=False)
print(f"\nSaved H3 predictions: data/processed/h2_test_predictions.csv")

# 9. Plot Calibration
from sklearn.calibration import calibration_curve
plt.figure(figsize=(8, 6))
plt.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")

for probs, name in [(X_test["market_price"], "Market Price"), (best_probs, f"ML ({best_name})")]:
    fraction_of_positives, mean_predicted_value = calibration_curve(y_test, probs, n_bins=10)
    plt.plot(mean_predicted_value, fraction_of_positives, "s-", label=name)

plt.ylabel("Fraction of positives")
plt.xlabel("Mean predicted probability")
plt.title("Calibration Curve v2 (Test Set: 2025-2026)")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig("results/h2_calibration_curve_v2.png", dpi=150)
print("Saved plot: results/h2_calibration_curve_v2.png")
print("\n=== DONE ===")