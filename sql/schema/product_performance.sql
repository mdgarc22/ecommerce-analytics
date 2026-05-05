-- Top 10 products by revenue
SELECT
	dp.stock_code,
    dp.product_category,
    dp.description,
    COUNT(DISTINCT fs.invoice_no) AS orders,
    SUM(fs.quantity) AS units_sold,
    ROUND(SUM(fs.total_amount), 2) AS revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_key = dp.product_key
WHERE fs.is_return = 0
GROUP BY dp.stock_code, dp.description, dp.product_category
ORDER BY revenue DESC
LIMIT 10;

-- Verify "Paper Craft, Little Birdie" order # is correct
SELECT
    fs.invoice_no,
    dd.full_date,
    dc.customer_id,
    dco.country_name,
    SUM(fs.quantity)            AS total_units,
    ROUND(SUM(fs.total_amount), 2) AS total_revenue
FROM fact_sales fs
JOIN dim_date     dd  ON fs.date_key     = dd.date_key
JOIN dim_customer dc  ON fs.customer_key = dc.customer_key
JOIN dim_country  dco ON fs.country_key  = dco.country_key
WHERE fs.invoice_no = '581483'
GROUP BY fs.invoice_no, dd.full_date, dc.customer_id, dco.country_name; 