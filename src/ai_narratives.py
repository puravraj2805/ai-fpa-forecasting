import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROCESSED = Path("data/processed")

def generate_cfo_narrative():
    var = pd.read_csv(PROCESSED / "variance_summary.csv").iloc[0].to_dict()

    prompt = f"""
You are a FAANG FP&A Director writing an executive summary.

Revenue change: {var['revenue_change']:.2f}
OPEX change: {var['opex_change']:.2f}
Margin change: {var['margin_change']:.2f}
Top region driver: {var['top_region_driver']}
Region delta: {var['top_region_delta']:.2f}

Write a concise CFO-ready explanation of what changed and why.
"""

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )

    narrative = resp.choices[0].message.content

    out = pd.DataFrame([{"executive_narrative": narrative}])
    out.to_csv(PROCESSED / "cfo_narrative.csv", index=False)

    print("\n🧠 CFO Narrative Generated:\n")
    print(narrative)

if __name__ == "__main__":
    generate_cfo_narrative()
