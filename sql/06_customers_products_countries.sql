-- =============================================================================
-- 06 · Revenue concentration, countries, products, returns and order timing
-- =============================================================================

-- Pareto curve: what share of revenue comes from the top X% of customers?
CREATE OR REPLACE TABLE customer_pareto AS
WITH per_customer AS (
    SELECT customer_id, sum(revenue) AS revenue
    FROM customer_sales
    GROUP BY customer_id
),
ranked AS (
    SELECT revenue,
           row_number() OVER (ORDER BY revenue DESC, customer_id)        AS rn,
           count(*)     OVER ()                                          AS n,
           sum(revenue) OVER ()                                          AS total,
           sum(revenue) OVER (ORDER BY revenue DESC, customer_id
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative
    FROM per_customer
)
SELECT rn                                   AS customer_rank,
       round(100.0 * rn / n, 2)             AS pct_customers,
       round(100.0 * cumulative / total, 2) AS cumulative_pct_revenue
FROM ranked
ORDER BY rn;

CREATE OR REPLACE TABLE country_revenue AS
SELECT country,
       round(sum(revenue), 0)                                       AS revenue,
       count(DISTINCT invoice)                                      AS orders,
       count(DISTINCT customer_id)                                  AS customers,
       round(100.0 * sum(revenue) / sum(sum(revenue)) OVER (), 2)   AS pct_revenue
FROM sales
GROUP BY country
ORDER BY revenue DESC;

-- Top products plus how often they get cancelled/returned.
-- The cancel rate is only shown for products with 500+ units sold: for tiny
-- products one return dominates, and a return can refer to a sale made before
-- the data starts (Dec 2009), which pushes the rate above 100%.
CREATE OR REPLACE TABLE product_performance AS
WITH sold AS (
    SELECT stock_code,
           arg_max(description, invoice_date) AS description,   -- latest name used
           sum(quantity)                      AS units_sold,
           sum(revenue)                       AS revenue,
           count(DISTINCT invoice)            AS orders
    FROM sales
    GROUP BY stock_code
),
cancelled AS (
    SELECT stock_code,
           sum(abs(quantity))   AS units_cancelled,
           sum(cancelled_value) AS cancelled_value
    FROM cancellations
    GROUP BY stock_code
)
SELECT s.stock_code,
       s.description,
       s.units_sold,
       round(s.revenue, 0)                                              AS revenue,
       s.orders,
       coalesce(c.units_cancelled, 0)                                   AS units_cancelled,
       CASE WHEN s.units_sold >= 500
            THEN round(100.0 * coalesce(c.units_cancelled, 0) / s.units_sold, 1)
       END                                                              AS cancel_rate_pct
FROM sold s
LEFT JOIN cancelled c USING (stock_code)
ORDER BY revenue DESC;

-- Overall value of cancellations relative to gross sales.
CREATE OR REPLACE TABLE cancellation_summary AS
SELECT round((SELECT sum(revenue) FROM sales), 0)                AS gross_sales,
       round((SELECT sum(cancelled_value) FROM cancellations), 0) AS cancelled_value,
       round(100.0 * (SELECT sum(cancelled_value) FROM cancellations)
                   / (SELECT sum(revenue) FROM sales), 1)          AS cancelled_pct_of_sales;

-- When do orders happen? (weekday x hour)
CREATE OR REPLACE TABLE order_timing AS
SELECT isodow(invoice_date)        AS weekday_num,      -- 1 = Monday
       dayname(invoice_date)       AS weekday,
       hour(invoice_date)          AS hour,
       count(DISTINCT invoice)     AS orders,
       round(sum(revenue), 0)      AS revenue
FROM sales
GROUP BY ALL
ORDER BY weekday_num, hour;

-- Headline numbers for the whole cleaned dataset (dashboard KPI tiles).
CREATE OR REPLACE TABLE headline_kpis AS
SELECT min(invoice_date)::DATE       AS first_day,
       max(invoice_date)::DATE       AS last_day,
       count(*)                      AS sales_lines,
       count(DISTINCT invoice)       AS orders,
       count(DISTINCT customer_id)   AS customers,
       count(DISTINCT stock_code)    AS products,
       round(sum(revenue), 0)        AS revenue,
       round(sum(revenue) / count(DISTINCT invoice), 2) AS avg_order_value
FROM sales;
