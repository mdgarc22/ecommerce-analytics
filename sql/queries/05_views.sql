-- Monthly revenue trend, MoM growth
-- View combines two window function queries: MoM growth and Cumulative revenue 
CREATE OR REPLACE VIEW vw_monthly_revenue AS
WITH monthly_revenue AS (
    SELECT
        dd.year,
        dd.month,
        dd.month_name,
        ROUND(SUM(fs.total_amount), 2) AS revenue,
        COUNT(DISTINCT fs.invoice_no) AS orders
    FROM fact_sales fs
    JOIN dim_date dd ON fs.date_key = dd.date_key
    WHERE fs.is_return = 0
    GROUP BY dd.year, dd.month, dd.month_name
)
SELECT
    year,
    month,
    month_name,
    revenue,
    orders,
    LAG(revenue) OVER (ORDER BY year, month)  AS prev_month_revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY year, month), 2) AS mom_change,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY year, month))
        / LAG(revenue) OVER (ORDER BY year, month) * 100, 2) AS mom_growth_pct,
    SUM(revenue) OVER (PARTITION BY year ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
FROM monthly_revenue
ORDER BY year, month;

-- Run this line for view above
-- Make sure view is created prior to running this SELECT query 
SELECT * FROM vw_monthly_revenue;



-- Product performance view
-- No CTE, window functions calls aggregate expression directly and not a column alias (CTE) defined
CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    dp.stock_code,
    dp.description,
    dp.product_category,
    ROUND(SUM(fs.total_amount), 2) AS revenue,
    SUM(fs.quantity) AS units_sold,
    COUNT(DISTINCT fs.invoice_no) AS orders,
    ROUND(AVG(fs.unit_price), 2) AS avg_unit_price,
    RANK() OVER (PARTITION BY dp.product_category 
    ORDER BY SUM(fs.total_amount) DESC) AS category_rank,
    RANK() OVER (ORDER BY SUM(fs.total_amount) DESC) AS overall_rank
FROM fact_sales fs
JOIN dim_product dp ON fs.product_key = dp.product_key
WHERE fs.is_return = 0
GROUP BY dp.stock_code, dp.description, dp.product_category; 

-- Run this line for view above
-- Make sure view is created prior to running this SELECT query 
SELECT * FROM vw_product_performance
ORDER BY overall_rank
LIMIT 10;



-- Customer Summary View
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
    dc.customer_id,
    dc.customer_segment,
    dc.first_purchase_date,
    dco.country_name,
    COUNT(DISTINCT fs.invoice_no) AS total_orders,
    ROUND(SUM(fs.total_amount), 2) AS total_revenue,
    ROUND(AVG(fs.total_amount), 2) AS avg_order_value,
    MIN(dd.full_date) AS first_order_date,
    MAX(dd.full_date) AS last_order_date,
    DATEDIFF(MAX(dd.full_date),MIN(dd.full_date)) AS customer_lifespan_days,
    RANK() OVER (PARTITION BY dc.customer_segment
        ORDER BY SUM(fs.total_amount) DESC) AS segment_rank,
    RANK() OVER (ORDER BY SUM(fs.total_amount) DESC) AS overall_rank
FROM fact_sales fs
JOIN dim_customer dc  ON fs.customer_key = dc.customer_key
JOIN dim_date     dd  ON fs.date_key     = dd.date_key
JOIN dim_country  dco ON fs.country_key  = dco.country_key
WHERE fs.is_return = 0
GROUP BY
    dc.customer_id,
    dc.customer_segment,
    dc.first_purchase_date,
    dco.country_name; 
    
-- Run this line for view above
-- Make sure view is created prior to running this SELECT query 
SELECT * FROM vw_customer_summary
ORDER BY overall_rank
LIMIT 10;



-- Revenue by country
CREATE OR REPLACE VIEW vw_country_revenue AS
SELECT
    dco.country_name,
    dco.region,
    ROUND(SUM(fs.total_amount), 2)          AS revenue,
    COUNT(DISTINCT fs.invoice_no)           AS orders,
    COUNT(DISTINCT fs.customer_key)         AS customers,
    ROUND(SUM(fs.total_amount) /
    COUNT(DISTINCT fs.invoice_no), 2)       AS avg_order_value
FROM fact_sales fs
JOIN dim_country dco ON fs.country_key = dco.country_key
WHERE fs.is_return = 0
GROUP BY dco.country_name, dco.region
ORDER BY revenue DESC;

-- run this select statement
SELECT * FROM vw_country_revenue
ORDER BY revenue DESC
LIMIT 10; 