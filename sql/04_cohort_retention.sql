-- =============================================================================
-- 04 · Monthly cohort retention
-- A customer's cohort is the month of their FIRST purchase.
-- Retention in month N = % of the cohort that bought again N months later.
-- Caveat: the Dec 2009 cohort also contains customers who were already buying
-- before the dataset starts, so it looks more loyal than a true "new" cohort.
-- =============================================================================
CREATE OR REPLACE TABLE cohort_retention AS
WITH first_purchase AS (
    SELECT customer_id,
           min(order_month) AS cohort_month
    FROM customer_sales
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
           s.customer_id,
           f.cohort_month,
           datediff('month', f.cohort_month, s.order_month) AS month_number
    FROM customer_sales s
    JOIN first_purchase f USING (customer_id)
    WHERE s.order_month < DATE '2011-12-01'          -- drop the partial month
),
cohort_size AS (
    SELECT cohort_month, count(*) AS customers
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT a.cohort_month,
       c.customers                                   AS cohort_size,
       a.month_number,
       count(*)                                      AS active_customers,
       round(100.0 * count(*) / c.customers, 1)      AS retention_pct
FROM activity a
JOIN cohort_size c USING (cohort_month)
WHERE a.cohort_month < DATE '2011-12-01'
GROUP BY a.cohort_month, c.customers, a.month_number
ORDER BY a.cohort_month, a.month_number;

-- Customer-weighted average retention at key checkpoints, across all cohorts
-- that are old enough to have reached that month (excluding the Dec 2009 cohort).
CREATE OR REPLACE TABLE retention_summary AS
SELECT month_number,
       round(100.0 * sum(active_customers) / sum(cohort_size), 1) AS avg_retention_pct,
       count(*)                                                    AS cohorts_included
FROM cohort_retention
WHERE month_number IN (1, 3, 6, 12)
  AND cohort_month > DATE '2009-12-01'
GROUP BY month_number
ORDER BY month_number;

-- Share of identified customers who placed more than one order (ever).
CREATE OR REPLACE TABLE repeat_rate AS
WITH per_customer AS (
    SELECT customer_id, count(DISTINCT invoice) AS orders
    FROM customer_sales
    GROUP BY customer_id
)
SELECT count(*)                                              AS customers,
       count(*) FILTER (WHERE orders > 1)                    AS repeat_customers,
       round(100.0 * count(*) FILTER (WHERE orders > 1) / count(*), 1) AS repeat_rate_pct
FROM per_customer;
