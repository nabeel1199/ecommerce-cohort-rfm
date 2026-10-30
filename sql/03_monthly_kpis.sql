-- =============================================================================
-- 03 · Monthly KPIs with month-over-month and year-over-year growth
-- Uses window functions (LAG) over a named window.
-- December 2011 is excluded: the data stops on 9 Dec 2011, so it is a partial
-- month and would look like a fake collapse in revenue.
-- `active_customers` counts identified customers only.
-- =============================================================================
CREATE OR REPLACE TABLE monthly_kpis AS
WITH m AS (
    SELECT order_month,
           sum(revenue)                AS revenue,
           count(DISTINCT invoice)     AS orders,
           count(DISTINCT customer_id) AS active_customers
    FROM sales
    WHERE order_month < DATE '2011-12-01'
    GROUP BY order_month
)
SELECT order_month,
       round(revenue, 2)                                                    AS revenue,
       orders,
       active_customers,
       round(revenue / orders, 2)                                           AS avg_order_value,
       round(100.0 * (revenue - lag(revenue) OVER w) / lag(revenue) OVER w, 1)         AS revenue_mom_pct,
       round(100.0 * (revenue - lag(revenue, 12) OVER w) / lag(revenue, 12) OVER w, 1) AS revenue_yoy_pct
FROM m
WINDOW w AS (ORDER BY order_month)
ORDER BY order_month;
