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
    
    
--  