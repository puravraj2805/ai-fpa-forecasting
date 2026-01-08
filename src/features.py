import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

def build_training_table():
    revenue = pd.read_csv(RAW / "revenue_monthly.csv", parse_dates=["month"])
    opex = pd.read_csv(RAW / "opex_monthly.csv", parse_dates=["month"])
    macro = pd.read_csv(RAW / "macro_drivers.csv", parse_dates=["month"])
    headcount = pd.read_csv(RAW / "headcount.csv", parse_dates=["month"])

    rev_total = revenue.groupby("month")["revenue"].sum().reset_index()
    opex_total = opex.groupby("month")["opex"].sum().reset_index()
    hc_total = headcount.groupby("month")["headcount"].sum().reset_index()

    df = rev_total.merge(opex_total, on="month")
    df = df.merge(hc_total, on="month")
    df = df.merge(macro, on="month")

    df["margin"] = df["revenue"] - df["opex"]
    df["margin_pct"] = df["margin"] / df["revenue"]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "training_table.csv", index=False)
    print("✅ Training table built!")

if __name__ == "__main__":
    build_training_table()
