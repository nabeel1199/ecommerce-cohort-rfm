-- =============================================================================
-- 05 · RFM customer segmentation
--   Recency   = days since the customer's last purchase
--   Frequency = number of distinct orders
--   Monetary  = total revenue
-- Each metric is scored 1-5 with NTILE(5) (5 = best), then mapped to segments.
-- Ties: many customers have exactly 1 order, so NTILE splits tied customers by
-- customer_id. Frequency scores are therefore approximate at the low end.
-- =============================================================================
CREATE OR REPLACE TABLE rfm AS
WITH snapshot AS (
    -- "Today" for the analysis = the day after the last invoice in the data.
    SELECT max(invoice_date)::DATE + 1 AS as_of FROM sales
),
base AS (
    SELECT customer_id,
           datediff('day', max(invoice_date)::DATE, (SELECT as_of FROM snapshot)) AS recency_days,
           count(DISTINCT invoice)                                                 AS frequency,
           round(sum(revenue), 2)                                                  AS monetary
    FROM customer_sales
    GROUP BY customer_id
),
scored AS (
    SELECT *,
           ntile(5) OVER (ORDER BY recency_days DESC, customer_id) AS r_score,  -- most recent -> 5
           ntile(5) OVER (ORDER BY frequency ASC,    customer_id) AS f_score,
           ntile(5) OVER (ORDER BY monetary ASC,     customer_id) AS m_score
    FROM base
)
SELECT *,
       CASE
           WHEN r_score >= 4 AND f_score >= 4                  THEN 'Champions'
           WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal'
           WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Promising'
           WHEN r_score = 3  AND f_score <= 2                  THEN 'Needs Attention'
           WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
           WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 3 THEN 'Hibernating (high value)'
           ELSE 'Lost'
       END AS segment
FROM scored;

CREATE OR REPLACE TABLE rfm_segments AS
SELECT segment,
       count(*)                                                          AS customers,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)                AS pct_customers,
       round(sum(monetary), 0)                                           AS revenue,
       round(100.0 * sum(monetary) / sum(sum(monetary)) OVER (), 1)      AS pct_revenue,
       round(avg(recency_days), 0)                                       AS avg_recency_days,
       round(avg(frequency), 1)                                          AS avg_orders,
       round(avg(monetary), 0)                                           AS avg_revenue_per_customer
FROM rfm
GROUP BY segment
ORDER BY revenue DESC;
