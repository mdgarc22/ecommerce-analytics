-- Month-over-Month Revenue Growth
 WITH monthly_revenue AS (
	SELECT 
		dd.year,
        dd.month, 
        dd.month_name,
        ROUND(SUM(fs.total_amount), 2) AS revenue
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
    LAG(revenue) OVER (ORDER BY year, month) AS prev_month_revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY year, month), 2) as mom_change,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY year, month))
    / LAG(revenue) OVER (ORDER BY year, month) * 100, 2) AS mom_growth_pct
    FROM monthly_revenue
    ORDER BY year, month;


    
-- Product Revenue Rank within Category
WITH product_revenue AS (
	SELECT
		dp.stock_code,
        dp.description,
        dp.product_category,
        ROUND(SUM(fs.total_amount)) AS revenue,
        SUM(fs.quantity) AS units_sold
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_key = dp.product_key
        WHERE fs.is_return = 0
        GROUP BY dp.stock_code, dp.description, dp.product_category
)
SELECT
	stock_code,
    description,
    product_category,
    revenue,
    units_sold,
    RANK() OVER (PARTITION BY product_category ORDER BY revenue DESC) AS category_rank
    FROM product_revenue
    ORDER BY product_category, category_rank;

-- Top 3 Product Revenue Rank per Category 
WITH product_revenue AS (
    SELECT
        dp.stock_code,
        dp.description,
        dp.product_category,
        ROUND(SUM(fs.total_amount), 2)  AS revenue,
        SUM(fs.quantity)                AS units_sold
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_key = dp.product_key
    WHERE fs.is_return = 0
    GROUP BY dp.stock_code, dp.description, dp.product_category
),
ranked_products AS (
    SELECT
        stock_code,
        description,
        product_category,
        revenue,
        units_sold,
        RANK() OVER (PARTITION BY product_category ORDER BY revenue DESC) AS category_rank
    FROM product_revenue
)
SELECT *
FROM ranked_products
WHERE category_rank <= 3
ORDER BY product_category, category_rank;     
    
    
    
--  Cumulative Revenue Running Total
WITH monthly_revenue AS (
	SELECT
		dd.year,
        dd.month,
        dd.month_name,
        ROUND(SUM(fs.total_amount)) AS revenue
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
    SUM(revenue) OVER (PARTITION BY year ORDER BY month ROWS BETWEEN UNBOUNDED 
    PRECEDING AND CURRENT ROW) AS cumulative_revenue
    FROM monthly_revenue
    ORDER BY year, month;



-- Customer Purchase Frequency
WITH customer_orders AS (
	SELECT
		dc.customer_id,
        dc.customer_segment,
        dco.country_name,
        COUNT(DISTINCT fs.invoice_no)          AS total_orders,
        ROUND(SUM(fs.total_amount), 2)         AS total_revenue,
        ROUND(AVG(fs.total_amount), 2)         AS avg_order_value,
        MIN(dd.full_date)                      AS first_order_date,
        MAX(dd.full_date)                      AS last_order_date
    FROM fact_sales fs
    JOIN dim_customer dc  ON fs.customer_key = dc.customer_key
    JOIN dim_date     dd  ON fs.date_key     = dd.date_key
    JOIN dim_country  dco ON fs.country_key  = dco.country_key
    WHERE fs.is_return = 0
    GROUP BY dc.customer_id, dc.customer_segment, dco.country_name
),
ranked_customers AS (
    SELECT
        customer_id,
        customer_segment,
        country_name,
        total_orders,
        total_revenue,
        avg_order_value,
        first_order_date,
        last_order_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_segment
            ORDER BY total_revenue DESC
        ) AS segment_rank
    FROM customer_orders
)
SELECT *
FROM ranked_customers
WHERE segment_rank <= 5
ORDER BY customer_segment, segment_rank;
    FROM fact_sales fs
    
        