"""Build the interactive dashboard (docs/index.html, served by GitHub Pages).

Usage:
    python src/build_dashboard.py      # reads the CSVs in exports/

The page is a single static HTML file: the data is embedded as JSON and the
charts are drawn in the browser with Plotly.js, so there is no server.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
OUT = ROOT / "docs" / "index.html"


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(EXPORTS / f"{name}.csv")


def records(df: pd.DataFrame) -> list:
    return json.loads(df.to_json(orient="records"))


def build_payload() -> dict:
    monthly = load("monthly_kpis")
    cohorts = load("cohort_retention")
    cohorts = cohorts[cohorts["month_number"].between(1, 12)]
    heat = cohorts.pivot(index="cohort_month", columns="month_number", values="retention_pct")
    sizes = cohorts.drop_duplicates("cohort_month").set_index("cohort_month")["cohort_size"]

    pareto = load("customer_pareto")
    # Down-sample the 5,850-point curve to ~1 point per 0.5% of customers.
    pareto = pareto.groupby((pareto["pct_customers"] * 2).round()).last().reset_index(drop=True)

    timing = load("order_timing")
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = list(range(int(timing["hour"].min()), int(timing["hour"].max()) + 1))
    tgrid = (timing.pivot(index="weekday", columns="hour", values="orders")
             .reindex(index=weekdays, columns=hours).fillna(0))

    countries = load("country_revenue")
    products = load("product_performance")
    quality = load("data_quality")
    repeat = load("repeat_rate").iloc[0]
    retention = load("retention_summary").set_index("month_number")["avg_retention_pct"]
    cancel = load("cancellation_summary").iloc[0]
    rfm = load("rfm_segments")
    head = load("headline_kpis").iloc[0]

    return {
        "kpis": {
            "revenue": float(head["revenue"]),
            "orders": int(head["orders"]),
            "customers": int(head["customers"]),
            "aov": float(head["avg_order_value"]),
            "repeat_rate": float(repeat["repeat_rate_pct"]),
            "m1_retention": float(retention[1]),
            "cancel_pct": float(cancel["cancelled_pct_of_sales"]),
            "top20_share": float(load("customer_pareto").query("pct_customers >= 20")
                                 .iloc[0]["cumulative_pct_revenue"]),
        },
        "monthly": records(monthly),
        "cohort": {
            "months": [pd.Timestamp(m).strftime("%b %Y") for m in heat.index],
            "sizes": [int(sizes[m]) for m in heat.index],
            "offsets": [int(c) for c in heat.columns],
            "z": [[None if pd.isna(v) else float(v) for v in row] for row in heat.values],
        },
        "rfm": records(rfm),
        "pareto": records(pareto),
        "timing": {"weekdays": weekdays, "hours": hours, "z": tgrid.astype(int).values.tolist()},
        "countries": records(countries[countries["country"] != "United Kingdom"].head(10)),
        "uk_share": float(countries.loc[countries["country"] == "United Kingdom", "pct_revenue"].iloc[0]),
        "products": records(products.head(15)),
        "quality": records(quality),
    }


if __name__ == "__main__":
    html = TEMPLATE.read_text().replace("__DATA__", json.dumps(build_payload(), separators=(",", ":")))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
