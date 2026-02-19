-- E-commerce Analytics Project Data Warehouse
-- Create database

-- Create object of (database, table, view, index) named ecommerce_dw (data warehouse)
CREATE DATABASE IF NOT EXISTS ecommerce_dw
-- Define how data is stored/interpreted
-- utf8mb4 is the Unicode character set, utf8 multi-byte 4 as opposed to 3
CHARACTER SET utf8mb4
-- Define how text is compared and sorted
-- Controls case sensitivity, accent sensitivity, alphabetical ordering
-- utf8.. character set, unicode is sorting rules, ci is case insensitive
COLLATE utf8mb4_unicode_ci;

-- Use the database
-- Tells MySQL all commands are to be ran within this db
-- Else MySQL wouldn't know what db to use
USE ecommerce_dw;

-- Verify database was created
SELECT DATABASE() AS current_database;
