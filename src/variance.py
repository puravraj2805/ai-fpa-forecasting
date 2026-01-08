import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

def variance_decomposition():
    rev = pd.read_csv(RAW / "revenue_monthly.csv", parse_dates=["month"])
    opex = pd.read_csv(RAW / "opex_monthly.csv", parse_dates=["month"])

    # Compare last two months
    last_two = sorted(rev["month"].unique())[-2:]
    m0, m1 = last_two[0], last_two[1]

    r0 = rev[rev["month"] == m0]["revenue"].sum()
    r1 = rev[rev["month"] == m1]["revenue"].sum()
    o0 = opex[opex["month"] == m0]["opex"].sum()
    o1 = opex[opex["month"] == m1]["opex"].sum()

    variance = {
        "revenue_change": r1 - r0,
        "opex_change": o1 - o0,
        "margin_change": (r1 - o1) - (r0 - o0)
    }

    # Biggest revenue driver
    by_region = rev.groupby(["month", "region"])["revenue"].sum().reset_index()
    pivot = by_region.pivot(index="region", columns="month", values="revenue").fillna(0)
    pivot["delta"] = pivot[m1] - pivot[m0]
    top_region = pivot["delta"].idxmax()

    variance["top_region_driver"] = top_region
    variance["top_region_delta"] = float(pivot.loc[top_region, "delta"])

    pd.DataFrame([variance]).to_csv(PROCESSED / "variance_summary.csv", index=False)
    print("✅ Variance decomposition complete!")

if __name__ == "__main__":
    variance_decomposition()
