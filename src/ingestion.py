from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Paths:
    root: Path = Path(__file__).resolve().parents[1]
    raw: Path = root / "data" / "raw"
    processed: Path = root / "data" / "processed"

def _month_range(start="2022-01-01", end="2025-12-01"):
    return pd.date_range(start=start, end=end, freq="MS")

def generate_synthetic_finance_data(seed=42):
    rng = np.random.default_rng(seed)
    months = _month_range()

    products = ["Core", "Plus", "Enterprise"]
    regions = ["NA", "EMEA", "APAC"]
    opex_cats = ["Cloud", "Sales", "Marketing", "G&A"]
    depts = ["Engineering", "Sales", "Marketing", "G&A"]

    macro = pd.DataFrame({
        "month": months,
        "inflation_idx": 100 + np.cumsum(rng.normal(0.15, 0.25, len(months))),
        "growth_idx": 100 + np.cumsum(rng.normal(0.2, 0.35, len(months)))
    })

    hc_rows = []
    for d in depts:
        base = {"Engineering":120,"Sales":80,"Marketing":40,"G&A":30}[d]
        trend = np.linspace(0,35,len(months))
        noise = rng.normal(0,3,len(months))
        hc = np.maximum(0, base + trend + noise).astype(int)
        avg = {"Engineering":17000,"Sales":16000,"Marketing":14000,"G&A":13000}[d]
        hc_rows.append(pd.DataFrame({"month":months,"department":d,"headcount":hc,"avg_monthly_cost":avg}))
    headcount = pd.concat(hc_rows)

    rev_rows = []
    for p in products:
        for r in regions:
            base = {"Core":450000,"Plus":220000,"Enterprise":160000}[p]
            region_mult = {"NA":1.15,"EMEA":0.95,"APAC":0.85}[r]
            season = 1 + 0.06*np.sin(np.linspace(0,8*np.pi,len(months)))
            macro_eff = (macro["growth_idx"]-100)/200
            shock = rng.normal(0,0.03,len(months))
            revenue = base * region_mult * season * (1 + macro_eff + shock)
            rev_rows.append(pd.DataFrame({"month":months,"product":p,"region":r,"revenue":np.round(revenue,2)}))
    revenue = pd.concat(rev_rows)

    total_rev = revenue.groupby("month")["revenue"].sum().reset_index(name="total_revenue")
    total_hc = headcount.groupby("month").apply(lambda d: pd.Series({
        "people_cost":(d["headcount"]*d["avg_monthly_cost"]).sum()
    })).reset_index()

    base = total_rev.merge(total_hc,on="month").merge(macro,on="month")

    opex_rows=[]
    for c in opex_cats:
        if c=="Cloud":
            spend = 0.13*base["total_revenue"]*(base["inflation_idx"]/100)
        elif c=="Sales":
            spend = 0.1*base["total_revenue"]
        elif c=="Marketing":
            spend = 0.06*base["total_revenue"]
        else:
            spend = 0.22*base["people_cost"]*(base["inflation_idx"]/100)
        opex_rows.append(pd.DataFrame({"month":months,"category":c,"opex":np.round(spend,2)}))
    opex = pd.concat(opex_rows)

    return {
        "macro_drivers":macro,
        "headcount":headcount,
        "revenue_monthly":revenue,
        "opex_monthly":opex
    }

def save_raw_tables(tables):
    Paths().raw.mkdir(parents=True, exist_ok=True)
    for n,df in tables.items():
        df.to_csv(Paths().raw/f"{n}.csv",index=False)

if __name__=="__main__":
    save_raw_tables(generate_synthetic_finance_data())
    print("✅ Finance dataset generated!")
