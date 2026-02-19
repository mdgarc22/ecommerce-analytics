-- E-commerce Analytics Project Data Warehouse
-- Create all dimension tables

-- State what db to use
USE ecommerce_dw;

DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_country;

-- Create customer dimension table
CREATE TABLE dim_customer (
-- Primary Key (Surrogate Key)
customer_key INT AUTO_INCREMENT PRIMARY KEY,
-- Natural Key from source data
customer_id INT,

-- customer attributes
first_purchase_date DATE,
country VARCHAR(100),
customer_segment VARCHAR(50),

-- Audit columns
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- Indexes for performance
INDEX idx_customer_id (customer_id)

) ENGINE=InnoDB COMMENT='Customer dimension table';

-- Create product dimension table
CREATE TABLE dim_product (
-- Primary key
product_key INT AUTO_INCREMENT PRIMARY KEY,

-- Natural key
stock_code VARCHAR(50),

-- Product attributes
description VARCHAR(500),
product_category VARCHAR(100),

-- Audit columns
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 

-- Index
INDEX idx_stock_code (stock_code)
) ENGINE=InnoDB COMMENT='Product dimension table';

-- Create dim_date table
CREATE TABLE dim_date (
-- Primary key
date_key INT PRIMARY KEY,

-- Natural key
full_date DATE NOT NULL,

-- Year attributes
year INT,
quarter INT,

-- Month attributes
month INT,
month_name VARCHAR(20),

-- Week attributes
week INT,

-- Day attributes
day_of_month INT,
day_of_week INT,
day_name VARCHAR(20),

-- Flags
is_weekend BOOLEAN,
is_holiday BOOLEAN DEFAULT FALSE,

-- Unique constraint on full_date
UNIQUE KEY idx_full_date (full_date)

) ENGINE=InnoDB COMMENT='Date dimension table';

-- Create dim_country table
CREATE TABLE dim_country (
-- Primary Key
country_key INT AUTO_INCREMENT PRIMARY KEY,

-- Attributes
country_name VARCHAR(100) UNIQUE,
region VARCHAR(100),

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

) ENGINE= InnoDB COMMENT='Country dimension table';

-- Verify tables are correct
SHOW TABLES;

DESCRIBE dim_customer;
DESCRIBE dim_product;
DESCRIBE dim_date;
DESCRIBE dim_country;