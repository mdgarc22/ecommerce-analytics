-- E-commerce Analytics Project Data Warehouse
-- Create fact table

-- Drop if table exists

-- Create
CREATE TABLE fact_sales (
-- Primary Key
sales_id INT AUTO_INCREMENT PRIMARY KEY,

-- Business Key from source data
invoice_no VARCHAR(50) NOT NULL,

-- Foreign keys to dimension tables
customer_key INT,
product_key INT NOT NULL,
date_key INT NOT NULL,
country_key INT NOT NULL,

-- Measures/Facts to analyze
quantity INT NOT NULL,
unit_price DECIMAL(10, 2) NOT NULL,
total_amount DECIMAL (12, 2) NOT NULL,

-- Flags
is_return BOOLEAN DEFAULT FALSE,

-- Audit
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

-- Foreign key constraints (referential integrity)

-- Links customer_key from fact table to customer_key on dim_customer
-- If customer is deleted records will remain but customer_key becomes NULL
-- CASCADE if, rare, pk changes in dimension then update fk in fact_table
CONSTRAINT fk_customer 
        FOREIGN KEY (customer_key) 
        REFERENCES dim_customer(customer_key)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

-- RESTRICT prevents deleting sales records that are referenced
-- Enforces data integrity
-- Must delete sales first then product
CONSTRAINT fk_product 
	FOREIGN KEY (product_key) 
	REFERENCES dim_product(product_key)
	ON DELETE RESTRICT
	ON UPDATE CASCADE,

CONSTRAINT fk_date 
	FOREIGN KEY (date_key) 
	REFERENCES dim_date(date_key)
	ON DELETE RESTRICT
	ON UPDATE CASCADE,

CONSTRAINT fk_country 
	FOREIGN KEY (country_key) 
	REFERENCES dim_country(country_key)
	ON DELETE RESTRICT
	ON UPDATE CASCADE,
    
-- Indexes (on fk and common query columns)
-- Provides for faster queries
INDEX idx_invoice_no (invoice_no),
INDEX idx_customer_key (customer_key),
INDEX idx_product_key (product_key),
INDEX idx_date_key (date_key),
INDEX idx_country_key (country_key),
INDEX idx_invoice_date (date_key, invoice_no)
    
) ENGINE=InnoDB COMMENT='Sales fact table - transactional data';

-- Verify table
DESCRIBE fact_sales;

SHOW TABLES;

-- FK relationships
SHOW CREATE TABLE fact_sales;