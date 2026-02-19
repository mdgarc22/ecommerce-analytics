# ETL PLAN for E-Commerce Data Warehouse

## EXTRACT Phase

### TASK: Load raw data from CSV
- read 'online_retail.csv' file
- convert InvoiceDate to datetime




## TRANSFORM Phase

### TASK 1: Data cleaning
Based off of EDA:

    Remove bad data:
        - Drop rows where CustomerID is null
            - Why
                - Breaks referential integrity
                - Makes customer-level analysis impossible
                - Can't link order to customer dimension
            - Impact
                - Null customer = orphaned fact
                - Fact tables should ALWAYS reference valid dimension keys
            - Possible Alternate Solutions
                - Route to an unknown customer instead of dropping
        - Remove cancelled orders
            - Why
                - Prevents inflation to revenue, order counts, conversion metrics. 
                - Not recogized as completed sales.
            - Impact
                - Prevents inaccurate KPIs
            - Possible Alternate Solutions
                - Keep in a seperate table for cancelled order info
        - Remove rows where Quanity <= 0
            - Why
                - Tends to be returns
                - Data entry error
            - Impact
                - Avoids errors in math logic
                - Aggreagations become misleading
            - Possible Alternate Solution
                - create a return table tracking all returns
        - Remove rows where UnitPrice <= 0
            - Why
                - Can be test transactions
                - Bad ingestion
                - Placeholder values
            - Impact
                - Prevent zero-revenue sales
                - Prevents negative revenue anomalies
        - Remove duplicate rows
            - Why
                - Avoid double-counted revenue
                - Causes inflated order volume
                - Provides incorrect customer lifetime value
            - Impact
                - Supports best practice for data warehouse
                    - facts must be atomic and unique
    
    Clean text data:
        - Strip whitespace from Description
            - Why
                - Avoid breaking Grouping, Joins, Deduplication
            - Impact
                - Ensures consistent dimension attributes
        - Convert description to uppercase
            - Why
                - Normalization for grouping and comparison
                - Prevents case-based duplicates
                - Supports backend logic
            - Impact
                - Cleaner product/category dimensions
                - Consistent BI filters
        - Clean StockCode (remove leading/trailing spaces)
            - Why
                - Natural key must avoid whitespace to avoid breaking joins between fact sales and product dimension
                - Keys must be EXACT match

    Create calculated fields:
        - Calculate total_amount = Quantity * UnitPrice
        - Create is_return flag (if Quantity was negative)

    Expected result after cleaning:
        - Original rows: ~541,000
        - After removing null CustomerID: ~400,000 (based on EDA: 25% nulls)
        - After removing cancelled/returns: ~380,000
        - After removing bad prices: ~378,000
        - After deduplication: ~375,000
        - Final cleaned rows: ~375,000

    
### TASK 2: Build Dimension Data
    Dimensions:
        - dim_customer
            - Get unique CustomerIDs
            - Calculate first_purchase_date for each customer
            - Get country for each customer
            - Assign customer_segment
        - dim_product
            - Get unique StockCode and Description combinations
            - Derive product category from Description keywords
                - If statements reading description
        - dim_date
            - Find min and max dates in dataset
            - Generate all dates in that range
            - Calculate year, quarter, month, day_of_week for each date
            - Create date_key as integer (yyyymmdd format) 
        - dim_country
            - Get unique countries
            - Manually assign regions

    Expected Outcomes:

    Dimensions:
        - dim_customer: ~4,300 rows (unique CustomerIDs after removing nulls)
        - dim_product: ~3,950 rows (unique StockCodes)
        - dim_date: ~365 rows (Dec 2010 - Dec 2011 = ~1 year)
        - dim_country: ~38 rows (unique countries)

    Fact:
        - fact_sales: ~375,000 rows (after cleaning)


## LOAD Phase

### Task 1: Load Dimensions
    Steps:
        - Load dim_date
            - Insert all date records
            - Verify row count matches expected
        - Load dim_country
            - Insert all countries
            - Verify unique countries loaded
        - Load dim_product
            - Insert all products with categories
            - Verify row count
        - Load dim_customer
            - Insert all customers
            - Verify row count
    
    Order Matters:
        - Date and Country have no dependencies
        - Product and Customer reference Country
        - Fact table references ALL dimensions


### Task 2: Load Fact Table
    Steps:
        - Join cleaned data to dimensions
            - Join to dim_customer to get customer_key
            - Join to dim_product to get product_key
            - Join to dim_date to get date_key
            - Join to dim_country to get country_key
        - Prepare fact table data
            - Select: invoice_no, customer_key, product_key, date_key, country_key
            - Include: quantity, unit_price, total_amount, is_return
        - Insert into fact_sales
            - Load all records
            - Verify row count matches cleaned data




## VALIDATION Phase

### After loading:
    Verify:
        - Row counts in each table
        - No NULL foreign keys in fact_sales (except customer_key)
        - Total revenue matches between csv and database
        - Sample queries returned expected results
        - No orphaned records

### Test:
    Queries:
        - Total revenue: 'SELECT SUM(total_amount) FROM fact_sales;'
        - Unique customers: 'SELECT COUNT(Distinct customer_key) FROM fact_sales;'
        - Date range: 'SELECT MIN(date_key), MAX(date_key) FROM fact_sales;'
        - Verify all foreign keys exist in dimensions:
            SELECT COUNT(*) 
            FROM fact_sales f
            LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
            WHERE c.customer_key IS NULL; 

