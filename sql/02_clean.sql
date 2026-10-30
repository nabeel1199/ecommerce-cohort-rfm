-- =============================================================================
-- 02 · Cleaning
-- Rules (the README explains why each one exists):
--   1. Drop exact duplicate rows (same invoice, product, quantity, time, price).
--   2. Keep real product lines only: stock codes that start with 5 digits.
--      This removes postage, Amazon fees, bank charges and manual adjustments.
--   3. A sale = a non-cancelled invoice line with quantity > 0 and price > 0.
--   4. Cancellations are kept in their own table so returns can be analysed.
--   5. Same-day full reversals are removed from BOTH sides. These are order-entry
--      mistakes (e.g. 80,995 paper crafts ordered and cancelled minutes later)
--      that would otherwise make random products look like best-sellers.
-- =============================================================================

CREATE OR REPLACE TABLE dedup AS
SELECT DISTINCT * FROM raw_retail;

-- A cancellation line that exactly undoes a sale line on the same day:
-- same customer, product, price and quantity.
CREATE OR REPLACE TABLE same_day_reversals AS
SELECT DISTINCT
       s.invoice      AS sale_invoice,
       c.invoice      AS cancel_invoice,
       s.stock_code,
       s.customer_id,
       s.quantity,
       s.unit_price,
       s.quantity * s.unit_price AS reversed_value,
       s.invoice_date AS sale_time,
       c.invoice_date AS cancel_time
FROM dedup s
JOIN dedup c
  ON  c.invoice LIKE 'C%'
  AND s.invoice NOT LIKE 'C%'
  AND s.customer_id = c.customer_id
  AND s.stock_code  = c.stock_code
  AND s.unit_price  = c.unit_price
  AND s.quantity    = -c.quantity
  AND c.invoice_date >= s.invoice_date
  AND c.invoice_date::DATE = s.invoice_date::DATE;

CREATE OR REPLACE TABLE sales AS
SELECT invoice,
       stock_code,
       description,
       quantity,
       invoice_date,
       unit_price,
       customer_id,
       country,
       quantity * unit_price                       AS revenue,      -- GBP
       date_trunc('month', invoice_date)::DATE     AS order_month
FROM dedup
WHERE invoice NOT LIKE 'C%'
  AND invoice NOT LIKE 'A%'
  AND regexp_matches(stock_code, '^[0-9]{5}')
  AND quantity > 0
  AND unit_price > 0
  AND (invoice, stock_code, quantity, unit_price) NOT IN (
        SELECT (sale_invoice, stock_code, quantity, unit_price) FROM same_day_reversals);

CREATE OR REPLACE TABLE cancellations AS
SELECT *,
       abs(quantity) * unit_price AS cancelled_value
FROM dedup
WHERE invoice LIKE 'C%'
  AND regexp_matches(stock_code, '^[0-9]{5}')
  AND (invoice, stock_code, -quantity, unit_price) NOT IN (
        SELECT (cancel_invoice, stock_code, quantity, unit_price) FROM same_day_reversals);

-- Customer-level analysis (cohorts, RFM) needs an identified customer.
CREATE OR REPLACE VIEW customer_sales AS
SELECT * FROM sales WHERE customer_id IS NOT NULL;
