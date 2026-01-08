import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression

PROCESSED = Path("data/processed")

def mape(y_true, y_pred) -> float:
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return float(np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), 1e-9))) * 100)

def train_driver_model(df: pd.DataFrame, target: str):
    """
    Simple driver-based forecasting model:
    Predict target using headcount + macro drivers.
    """
    features = ["headcount", "inflation_idx", "growth_idx"]
    X = df[features].values
    y = df[target].values

    model = LinearRegression()
    model.fit(X, y)
    return model, features

def forecast_next_month(df: pd.DataFrame, model: LinearRegression, features: list[str]):
    last = df.sort_values("month").iloc[-1].copy()

    # naive forward assumptions (baseline):
    # headcount grows slightly, macro continues trend
    last["headcount"] = last["headcount"] * 1.01
    last["inflation_idx"] = last["inflation_idx"] * 1.002
    last["growth_idx"] = last["growth_idx"] * 1.003

    X_next = np.array([[last[f] for f in features]])
    pred = float(model.predict(X_next)[0])
    return pred, last

def run_baseline_forecast():
    df = pd.read_csv(PROCESSED / "training_table.csv", parse_dates=["month"])
    df = df.sort_values("month")

    # Train / test split (last 6 months as test)
    train = df.iloc[:-6].copy()
    test = df.iloc[-6:].copy()

    # Train revenue + opex models
    rev_model, rev_feats = train_driver_model(train, "revenue")
    opex_model, opex_feats = train_driver_model(train, "opex")

    # Predict on test set
    test_X = test[rev_feats].values
    test["rev_pred"] = rev_model.predict(test_X)

    test_X2 = test[opex_feats].values
    test["opex_pred"] = opex_model.predict(test_X2)

    test["margin_pred"] = test["rev_pred"] - test["opex_pred"]

    # Accuracy
    rev_mape = mape(test["revenue"], test["rev_pred"])
    opex_mape = mape(test["opex"], test["opex_pred"])
    margin_mape = mape(test["margin"], test["margin_pred"])

    print("✅ Baseline Driver Model Accuracy (last 6 months)")
    print(f"Revenue MAPE: {rev_mape:.2f}%")
    print(f"OPEX   MAPE: {opex_mape:.2f}%")
    print(f"Margin MAPE: {margin_mape:.2f}%")

    # Next-month forecast
    next_rev, assumed_next = forecast_next_month(df, rev_model, rev_feats)
    next_opex, _ = forecast_next_month(df, opex_model, opex_feats)
    next_margin = next_rev - next_opex

    out = pd.DataFrame([{
        "month": (df["month"].max() + pd.offsets.MonthBegin(1)),
        "revenue_forecast": next_rev,
        "opex_forecast": next_opex,
        "margin_forecast": next_margin,
        "assumed_headcount": assumed_next["headcount"],
        "assumed_inflation_idx": assumed_next["inflation_idx"],
        "assumed_growth_idx": assumed_next["growth_idx"],
    }])

    out.to_csv(PROCESSED / "next_month_forecast.csv", index=False)
    print("\n📌 Next-month forecast saved to data/processed/next_month_forecast.csv")

if __name__ == "__main__":
    run_baseline_forecast()
