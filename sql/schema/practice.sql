-- What do I want to measure? → determines your aggregate functions in SELECT
-- What do I want to slice it by? → determines your GROUP BY
-- Where does that data live? → determines your FROM and JOINs
-- Do I need to exclude anything? → determines your WHERE
-- How should results be ordered? → determines your ORDER BY
-- How do I get only the top 10? → what goes in ORDER BY and LIMIT

-- count amount of rows from fact_sales table
select count(*) as fact_sales from fact_sales;
-- count all dim tables individually
select count(*) as dim_customer from dim_customer;
select count(*) as dim_product from dim_product;
select count(*) as dim_country from dim_country;
select count(*) as dim_date from dim_date;
-- count amount of rows from all dimension table
select (select count(*) from dim_customer) +
(select count(*) from dim_product) +
(select count(*) from dim_country) +
(select count(*) from dim_date) AS dim_tbl_count;

SELECT * FROM dim_product WHERE stock_code IN ('POST', 'M');
