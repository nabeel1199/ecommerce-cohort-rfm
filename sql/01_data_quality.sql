-- =============================================================================
-- 01 · Data quality profile
-- Before analysing anything, measure what is wrong with the raw data.
-- `raw_retail` is a view over the Parquet file, created in src/pipeline.py.
-- =============================================================================
CREATE OR REPLACE TABLE data_quality AS
WITH totals AS (
    SELECT count(*) AS n FROM raw_retail
),
checks AS (
    SELECT 1 AS ord, 'Exact duplicate rows' AS check_name,
           (SELECT count(*) FROM raw_retail)
         - (SELECT count(*) FROM (SELECT DISTINCT * FROM raw_retail)) AS rows_affected
    UNION ALL
    SELECT 2, 'Missing customer ID',
           count(*) FILTER (WHERE customer_id IS NULL) FROM raw_retail
    UNION ALL
    SELECT 3, 'Cancellation lines (invoice starts with "C")',
           count(*) FILTER (WHERE invoice LIKE 'C%') FROM raw_retail
    UNION ALL
    SELECT 4, 'Bad-debt adjustments (invoice starts with "A")',
           count(*) FILTER (WHERE invoice LIKE 'A%') FROM raw_retail
    UNION ALL
    SELECT 5, 'Non-product stock codes (postage, fees, manual entries)',
           count(*) FILTER (WHERE NOT regexp_matches(stock_code, '^[0-9]{5}')) FROM raw_retail
    UNION ALL
    SELECT 6, 'Zero or negative quantity',
           count(*) FILTER (WHERE quantity <= 0) FROM raw_retail
    UNION ALL
    SELECT 7, 'Zero or negative unit price',
           count(*) FILTER (WHERE unit_price <= 0) FROM raw_retail
    UNION ALL
    -- Measured properly in 02_clean.sql (same_day_reversals); here we just flag
    -- suspiciously large single lines, which is how the reversals were spotted.
    SELECT 8, 'Single lines with 10,000+ units (possible entry errors)',
           count(*) FILTER (WHERE abs(quantity) >= 10000) FROM raw_retail
)
SELECT check_name,
       rows_affected,
       round(100.0 * rows_affected / totals.n, 2) AS pct_of_rows
FROM checks, totals
ORDER BY ord;
