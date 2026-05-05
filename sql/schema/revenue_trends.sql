-- Monthly Revenue Trend
SELECT
	dd.year,
    dd.month,
    dd.month_name,
    ROUND(SUM(fs.total_amount), 2) AS revenue,
    -- distinct = unique 
    COUNT(DISTINCT fs.invoice_no) AS orders,
    ROUND(SUM(fs.total_amount) / COUNT(DISTINCT fs.invoice_no), 2) AS avg_order_value
FROM fact_sales fs
JOIN dim_date dd ON fs.date_key = dd.date_key
WHERE fs.is_return = 0
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;