# Rebuilding the dashboard in Tableau Public

Tableau Public is free and runs on macOS. The CSVs in `exports/` are already aggregated, so every sheet below takes a few minutes. Publish the finished workbook to your Tableau Public profile and link it from the README.

## 1. Connect the data

1. Run `python src/pipeline.py` so that `exports/` is up to date.
2. In Tableau Public, go to **Connect → Text file** and pick `exports/monthly_kpis.csv`.
3. Add each of these files as **separate data sources** (Data → New Data Source). They are at different grains, so don't join them:
   - `cohort_retention.csv`
   - `rfm_segments.csv`
   - `customer_pareto.csv`
   - `country_revenue.csv`
   - `product_performance.csv`
   - `order_timing.csv`
   - `headline_kpis.csv`
4. Check the field types. `order_month` and `cohort_month` should be **Date**. `customer_id` and `stock_code` should be **String**.

## 2. Sheets

| Sheet | Data source | Build |
|---|---|---|
| **KPI tiles** | headline_kpis | One sheet per KPI. Put `revenue` (or `orders`, `customers`, `avg_order_value`) on **Text**, set the format to £ / number, and increase the font size. |
| **Monthly revenue** | monthly_kpis | `MONTH(order_month)` (continuous, green) on Columns and `SUM(revenue)` on Rows, as a Line with markers. Put `orders` and `revenue_mom_pct` on Tooltip. |
| **Cohort heatmap** | cohort_retention | `cohort_month` (discrete month) on Rows and `month_number` (discrete) on Columns. Filter `month_number` to 1–12. Mark = Square; `AVG(retention_pct)` on **Color** (sequential Blue) and on **Label**. |
| **RFM segments** | rfm_segments | Measure Names on Color. Measure Values (`pct_customers`, `pct_revenue`) on Columns and `segment` on Rows, as side-by-side bars. Sort `segment` by `pct_revenue`. |
| **Pareto curve** | customer_pareto | `pct_customers` on Columns (continuous, dimension) and `cumulative_pct_revenue` on Rows, as a Line. Add a reference line at x = 20. |
| **Orders heatmap** | order_timing | `hour` on Columns and `weekday` on Rows (sort by `weekday_num`). Square marks with `SUM(orders)` on Color. |
| **Top markets** | country_revenue | Filter out United Kingdom. `country` on Rows and `pct_revenue` on Columns, as bars. Top 10 by `revenue`. |
| **Products** | product_performance | Text table with `description`, `revenue`, `units_sold` and `cancel_rate_pct`. Top 15 by `revenue`. |

## 3. Dashboard

- Size: **Automatic** (or 1200 × 1600), with the KPI tiles across the top.
- Order: monthly revenue → cohort heatmap → RFM and Pareto side by side → orders heatmap and top markets → products table.
- Add a text box with 3–4 key findings from the README. Recruiters read the text before the charts.
- Add an action filter: clicking a segment in the RFM chart highlights it.

## 4. Publish

**File → Save to Tableau Public**. Name it "Online Retail – Cohorts & RFM", then add the link to the README and to the "Projects" line on your CV.

> Power BI Desktop only runs on Windows. On a Mac, either use Tableau Public (above) or rebuild the same sheets in Power BI on a Windows machine or VM. The same CSVs work unchanged.
