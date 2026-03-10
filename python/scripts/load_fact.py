#  imports
# logging for debugging
import logging
# pathlib for file paths
from pathlib import Path
# typing for type hints
from typing import Optional

# pandas for data manipulation
import pandas as pd

# import databasemanager class
from db_config import DatabaseManager

#  configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# file paths
# relative path resolution
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLEANED_DATA_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'cleaned_data.csv'

# batch processing chunk size
# pandas will send 10000 rows at a time to the db
# this helps prevent any hinderrances with memory or database timeouts when loading large datasets along with performance benefits of batch loading
CHUNK_SIZE = 10_000

# read surrogate keys from dim table
def load_dimension_lookups(db: DatabaseManager) -> dict:
    # log
    logger.info('Loading dimension lookup tables')

    # surrogate key and natural key dictionary
    # these will be used on joins
    lookups = {
        'customer': db.read_sql('SELECT customer_key, customer_id FROM dim_customer'),
        'product':  db.read_sql('SELECT product_key, stock_code FROM dim_product'),
        'date':     db.read_sql('SELECT date_key, full_date FROM dim_date'),
        'country':  db.read_sql('SELECT country_key, country_name FROM dim_country'),
    }

    # loop and raise any errors
    for name, df in lookups.items():
        if df is None:
            raise ValueError(f'Failed to load {name} lookup — is dim_{name} populated?')
        logger.info('  %-12s %d rows', name, len(df))
    
    logger.info('Dimension lookups loaded successfully')
    return lookups

# build fact sales table
def build_fact_sales(df: pd.DataFrame, lookups: dict) -> pd.DataFrame:
    # log
    logger.info('Building fact sales table')

    # standardize join keys before merging
    # copy df to avoid modifying original df thats in memory
    # always copy before transforming in a function
    # immutable data flow
    df =df.copy()

    # CustomerID may load from CSV as float, convert to int then string
    # When Pandas reads a CSV, Int columns with nulls get loaded as floats
    df['CustomerID'] = df['CustomerID'].astype(float).astype(int).astype(str)

    # Standardize StockCode and Country
    # Standardized the same way when building dimensions
    df['StockCode'] = df['StockCode'].astype(str).str.strip().str.upper()
    df['Country'] = df['Country'].astype(str).str.strip()

    # Normalize InvoiceDate to date only
    # InvoiceDate has timestamps, full_date within dim_cate has pure dates and timestamp would cause an issue with matching
    # Store in a new column to preserve original timestamp
    df['join_date'] = pd.to_datetime(df['InvoiceDate']).dt.normalize()

    
    # Standardize dimension lookup keys to match
    # bilateral normalization, standardize both sides of the join to ensure they match
    # copy lookups to avoid modifying original dfs in memory
    customer_lkp = lookups['customer'].copy()
    customer_lkp['customer_id'] = customer_lkp['customer_id'].astype(str)

    product_lkp = lookups['product'].copy()
    product_lkp['stock_code'] = product_lkp['stock_code'].astype(str).str.strip().str.upper()

    date_lkp = lookups['date'].copy()
    date_lkp['full_date'] = pd.to_datetime(date_lkp['full_date']).dt.normalize()

    country_lkp = lookups['country'].copy()
    country_lkp['country_name'] = country_lkp['country_name'].astype(str).str.strip()

    # Surrogate key joins
    logger.info('Joining surrogate keys')

    # each merge adds surrogate key column to transactions df
    fact = (
        df
        .merge(customer_lkp.rename(columns={'customer_id': 'CustomerID'}),
               on='CustomerID', how='left')
        .merge(product_lkp.rename(columns={'stock_code': 'StockCode'}),
               on='StockCode', how='left')
        .merge(date_lkp.rename(columns={'full_date': 'join_date'}),
               on='join_date', how='left')
        .merge(country_lkp.rename(columns={'country_name': 'Country'}),
               on='Country', how='left')
    )

    # check for and drop unresolved keys
    key_columns = {
        'customer_key': 'customer',
        'product_key':  'product',
        'date_key':     'date',
        'country_key':  'country',
    }

    # data quality check
    # loop through each key column and log any missing matches before dropping
    for col, label in key_columns.items():
        # counts null values in each column
        missing = fact[col].isna().sum()
        # atomicity, one null=none otherwise all
        # in this instance, we want to know which keys are missing and how many, so we can log that information before dropping
        if missing > 0:
            logger.warning('%d rows could not match a %s key', missing, label)

    # length of rows before dropping
    rows_before = len(fact)
    # remove rows with any null sorrogate keys
    fact = fact.dropna(subset=list(key_columns.keys()))
    rows_after = len(fact)

    # log results of dropping
    # row count reconciliation, standard checkpoint in ETL pipelines
    if rows_before != rows_after:
        logger.warning('Dropped %d rows due to unresolvable keys', rows_before - rows_after)
    else:
        logger.info('All rows matched successfully — no keys dropped')

    # schema projection
    # specify only the columns we want in the final fact table and rename for consistency
    fact_sales = fact[[
        'InvoiceNo',
        'customer_key',
        'product_key',
        'date_key',
        'country_key',
        'Quantity',
        'UnitPrice',
        'total_amount',
        'is_return',
    ]].rename(columns={
        'InvoiceNo':  'invoice_no',
        'Quantity':   'quantity',
        'UnitPrice':  'unit_price',
    }).copy()

    # Cast surrogate keys to integer, left joins can produce floats
    for col in ['customer_key', 'product_key', 'date_key', 'country_key']:
        fact_sales[col] = fact_sales[col].astype(int)

    logger.info('fact_sales built: %d rows', len(fact_sales))
    return fact_sales

# load fact table
def load_fact_sales(fact_sales: pd.DataFrame, db: DatabaseManager) -> None:
    # log
    logger.info('Loading fact_sales table')

    # truncate first
    db.execute_query('SET FOREIGN_KEY_CHECKS = 0')
    db.execute_query('TRUNCATE TABLE fact_sales')
    db.execute_query('SET FOREIGN_KEY_CHECKS = 1')
    logger.info('Truncated fact_sales')

    # Bulk insert in chunks
    # method:multi tells panda to send mulitple rows at a time rather than one
    # chunk_size being 10,000 means it will send 10,000 rows at a time until all rows are sent
    # bulk loading
    engine = db.get_engine()
    fact_sales.to_sql(
        'fact_sales',
        engine,
        if_exists='append',
        index=False,
        chunksize=CHUNK_SIZE,
        method='multi',
    )
    logger.info('Loaded %d rows into fact_sales', len(fact_sales))


def validate_fact_load(fact_sales: pd.DataFrame, db: DatabaseManager) -> None:
    # log
    logger.info('Validating fact_sales load')

    # row count check
    result = db.read_sql('SELECT COUNT(*) AS cnt FROM fact_sales')
    # iloc = integer location
    # count the rows returned from db.read_sql
    db_count = int(result.iloc[0, 0])
    src_count = len(fact_sales)
    # log
    logger.info('Row count  — source: %d | database: %d', src_count, db_count)
    if db_count == src_count:
        logger.info('Row counts match')
    else:
        logger.info('Row counts mismatch')

    # revenue total
    result = db.read_sql('SELECT ROUND(SUM(total_amount), 2) AS rev FROM fact_sales')
    db_revenue = float(result.iloc[0, 0])
    src_revenue = round(float(fact_sales['total_amount'].sum()), 2)
    diff_pct = abs(src_revenue - db_revenue) / src_revenue * 100
    logger.info('Revenue — source: £%.2f | database: £%.2f | Δ %.4f%%',
                src_revenue, db_revenue, diff_pct)
    if diff_pct < 0.01:
        logger.info('Revenue totals match')
    else:
        logger.warning('Revenue mismatch exceeds 0.01%% threshold')

    # referential integrity
    orphan_check = db.read_sql("""
        SELECT
            SUM(CASE WHEN c.customer_key IS NULL THEN 1 ELSE 0 END) AS orphan_customers,
            SUM(CASE WHEN p.product_key  IS NULL THEN 1 ELSE 0 END) AS orphan_products,
            SUM(CASE WHEN d.date_key     IS NULL THEN 1 ELSE 0 END) AS orphan_dates,
            SUM(CASE WHEN co.country_key IS NULL THEN 1 ELSE 0 END) AS orphan_countries
        FROM fact_sales f
        LEFT JOIN dim_customer c  ON f.customer_key = c.customer_key
        LEFT JOIN dim_product  p  ON f.product_key  = p.product_key
        LEFT JOIN dim_date     d  ON f.date_key      = d.date_key
        LEFT JOIN dim_country  co ON f.country_key   = co.country_key
    """)
    row = orphan_check.iloc[0]
    for col in row.index:
        count  = int(row[col])
        status = '✓' if count == 0 else '✗'
        logger.info('  %s %-25s %d', status, col, count)

# testing
def main() -> None:
    logger.info('=' * 60)
    logger.info('LOAD FACT SCRIPT')
    logger.info('=' * 60)

    db = None

    try:
        # STEP 1: Load cleaned data
        logger.info('Loading cleaned data from: %s', CLEANED_DATA_PATH)
        df = pd.read_csv(CLEANED_DATA_PATH, parse_dates=['InvoiceDate'])
        logger.info('Loaded %d rows', len(df))

        # STEP 2: Connect to database
        db = DatabaseManager()
        db.connect()

        # STEP 3: Load dimension surrogate keys
        lookups = load_dimension_lookups(db)

        # STEP 4: Build fact_sales DataFrame
        fact_sales = build_fact_sales(df, lookups)

        # STEP 5: Load into MySQL
        load_fact_sales(fact_sales, db)

        # STEP 6: Validate
        validate_fact_load(fact_sales, db)

        logger.info('=' * 60)
        logger.info('LOAD FACT COMPLETE')
        logger.info('=' * 60)

    except Exception as e:
        logger.error('Fact load failed: %s', e, exc_info=True)
        raise

    finally:
        if db:
            db.disconnect()


if __name__ == '__main__':
    main()

