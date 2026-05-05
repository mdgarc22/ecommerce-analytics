-- What countries generate the most revenue?
SELECT
	dco.country_name,
    dco.region,
    ROUND(SUM(fs.total_amount), 2) AS revenue,
    COUNT(DISTINCT fs.invoice_no) AS orders,
    COUNT(DISTINCT fs.customer_key) AS customers
FROM fact_sales fs
JOIN dim_country dco ON fs.country_key = dco.country_key
WHERE fs.is_return = 0
GROUP BY dco.country_name, dco.region
ORDER BY revenue DESC;