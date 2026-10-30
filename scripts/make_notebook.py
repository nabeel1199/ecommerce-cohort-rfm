"""Generate and execute notebooks/analysis.ipynb (the walkthrough of the analysis).

Usage:
    python scripts/make_notebook.py
"""
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "analysis.ipynb"

md = nbformat.v4.new_markdown_cell
code = nbformat.v4.new_code_cell

cells = [
    md("# Online Retail II: cohort retention and RFM segmentation\n\n"
       "A walkthrough of the analysis. All of the logic lives in the SQL files under `sql/`. "
       "This notebook runs them with DuckDB and looks at the results.\n\n"
       "**Business questions**\n"
       "1. How healthy is the raw data, and what has to be cleaned?\n"
       "2. How does revenue move over time? Is there seasonality?\n"
       "3. Do new customers come back? (cohort retention)\n"
       "4. Which customers matter most, and who is about to churn? (RFM)\n"
       "5. How concentrated is revenue across customers, countries and products?"),
    code("import sys\nfrom pathlib import Path\n\n"
         "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
         "sys.path.insert(0, str(ROOT / 'src'))\n\n"
         "import pandas as pd\nfrom pipeline import build\n\n"
         "pd.set_option('display.width', 140)\n"
         "con = build()\n"
         "sql = lambda q: con.sql(q).df()"),
    md("## 1. Data quality\nMeasured on the raw file before any cleaning (`sql/01_data_quality.sql`)."),
    code("sql('SELECT * FROM data_quality')"),
    md("About 23% of lines have no customer ID. They are kept for revenue totals but left out of "
       "customer-level analysis (cohorts, RFM). The 15 lines with 10,000+ units led to an extra rule: "
       "orders that were cancelled in full on the same day are entry mistakes, so both sides are removed."),
    code("sql('''SELECT count(*) AS reversed_lines,\n"
         "              round(sum(reversed_value)) AS reversed_value_gbp\n"
         "       FROM same_day_reversals''')"),
    code("sql('''SELECT stock_code, quantity, unit_price, sale_time, cancel_time\n"
         "       FROM same_day_reversals ORDER BY reversed_value DESC LIMIT 5''')"),
    md("## 2. Clean dataset"),
    code("sql('SELECT * FROM headline_kpis')"),
    md("## 3. Revenue over time"),
    code("sql('SELECT * FROM monthly_kpis')"),
    md("Revenue roughly triples between the quietest months (Feb/Apr) and November. "
       "Nov 2011 is only 1.4% above Nov 2010, so year-on-year growth is flat at the peak."),
    md("## 4. Cohort retention"),
    code("sql('SELECT * FROM retention_summary')"),
    code("heat = sql('SELECT * FROM cohort_retention WHERE month_number BETWEEN 1 AND 12')\n"
         "heat.pivot(index='cohort_month', columns='month_number', values='retention_pct')"),
    md("Average retention is roughly flat at about 20% from month 1 to month 3, then about 18% to month 12. "
       "Customers who stay tend to keep buying, but most new customers never come back in a given month. "
       "The autumn 2010 cohorts jump at month 12, so seasonal gift buyers return for the next Christmas."),
    code("sql('SELECT * FROM repeat_rate')"),
    md("## 5. RFM segmentation"),
    code("sql('SELECT * FROM rfm_segments')"),
    code("sql('''SELECT segment, r_score, f_score, count(*) AS customers\n"
         "       FROM rfm GROUP BY ALL ORDER BY r_score DESC, f_score DESC LIMIT 10''')"),
    md("## 6. Concentration: customers, countries, products"),
    code("sql('SELECT * FROM customer_pareto WHERE pct_customers IN (1, 5, 10, 20, 50)')"),
    code("sql('SELECT * FROM country_revenue LIMIT 8')"),
    code("sql('SELECT * FROM product_performance LIMIT 10')"),
    code("sql('''SELECT * FROM product_performance\n"
         "       WHERE cancel_rate_pct IS NOT NULL\n"
         "       ORDER BY cancel_rate_pct DESC LIMIT 5''')"),
    code("sql('SELECT * FROM cancellation_summary')"),
    md("## 7. Recommendations\n"
       "- **Win back \"At Risk\" customers** (frequent buyers who have gone quiet). "
       "They are about 14% of customers and almost £1.5M of past revenue.\n"
       "- **Protect the Champions.** A quarter of customers bring in about 70% of revenue, "
       "so account management and early access to stock for the Q4 rush are worth it.\n"
       "- **Plan stock and staffing for Sept–Nov**, when revenue nearly triples.\n"
       "- **Look into high-return products** (e.g. the pantry chopping board at 82% returned) "
       "before reordering them.\n"
       "- **Collect customer IDs on every order.** About 13% of revenue cannot be linked to a customer.\n\n"
       "**Limitations:** single retailer, mostly wholesale buyers, 2 years of data, "
       "and no cost data, so this looks at revenue only, not profit."),
]

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
OUT.parent.mkdir(exist_ok=True)
NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(OUT.parent)}}).execute()
nbformat.write(nb, OUT)
print(f"Wrote {OUT}")
