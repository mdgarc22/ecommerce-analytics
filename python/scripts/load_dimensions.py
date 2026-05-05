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
CLEANED_DIR = PROJECT_ROOT / 'data' / 'cleaned'

# dynamically resolve the most recently created cleaned file
# glob pattern matches any timestamped cleaned_data file
# max() with st_mtime selects the most recently modified file
CLEANED_DATA_PATH = max(CLEANED_DIR.glob('cleaned_data_*.csv'), key=lambda f: f.stat().st_mtime)

# Country to region mapping
# Used as a lookup table to provide data enrichment
REGION_MAP = {
    'United Kingdom': 'Western Europe',
    'EIRE': 'Western Europe',
    'Channel Islands': 'Western Europe',
    'Germany': 'Western Europe',
    'France': 'Western Europe',
    'Netherlands': 'Western Europe',
    'Belgium': 'Western Europe',
    'Switzerland': 'Western Europe',
    'Austria': 'Western Europe',
    'Spain': 'Southern Europe',
    'Portugal': 'Southern Europe',
    'Italy': 'Southern Europe',
    'Greece': 'Southern Europe',
    'Cyprus': 'Southern Europe',
    'Malta': 'Southern Europe',
    'Norway': 'Northern Europe',
    'Sweden': 'Northern Europe',
    'Denmark': 'Northern Europe',
    'Finland': 'Northern Europe',
    'Iceland': 'Northern Europe',
    'Poland': 'Eastern Europe',
    'Czech Republic': 'Eastern Europe',
    'Lithuania': 'Eastern Europe',
    'USA': 'North America',
    'Canada': 'North America',
    'Australia': 'Oceania',
    'Japan': 'Asia',
    'Singapore': 'Asia',
    'Hong Kong': 'Asia',
    'Israel': 'Middle East',
    'Lebanon': 'Middle East',
    'Bahrain': 'Middle East',
    'Saudi Arabia': 'Middle East',
    'United Arab Emirates': 'Middle East',
    'Brazil': 'South America',
    'South Africa': 'Africa',
    'Nigeria': 'Africa',
    'RSA': 'Africa',
    'European Community': 'Western Europe',
    'Unspecified': 'Unknown',
}

# helper functions
# truncate a table before reloading/loading data
# truncation helps with idempotency ensuring that the script can be run multiple times without creating duplicate records
def truncate_table(db: DatabaseManager, table: str) -> None:
    # temporarily disble foreign key checks to allow truncation without constraint issues
    db.execute_query('SET FOREIGN_KEY_CHECKS = 0')
    # truncate the specified table to remove existing data and reset auto-increment counters
    db.execute_query(f'TRUNCATE TABLE {table}')
    # re-enable foreign key checks after truncation to maintain referential integrity
    db.execute_query('SET FOREIGN_KEY_CHECKS = 1')
    logger.info('Truncated table: %s', table)

# data enrichment function
# categorize products
def categorize_product(description: str) -> str:
    # validate input isnt null to prevent errors
    if not isinstance(description, str):
        return 'Uncategorized'
    
    # defensive transformation: previously done in data cleaning but doing again for safety net
    desc = description.upper()

    # create derived attributes
    # if logic to categorize products

    if any(k in desc for k in ['BAG', 'PURSE', 'TOTE', 'HANDBAG']):
        return 'Bags & Purses'
    if any(k in desc for k in ['MUG', 'CUP', 'BOWL', 'PLATE', 'KITCHEN', 'CAKE', 'GLASS']):
        return 'Kitchen & Dining'
    if any(k in desc for k in ['CANDLE', 'HOLDER', 'LANTERN', 'LIGHT', 'LAMP']):
        return 'Lighting & Candles'
    if any(k in desc for k in ['CARD', 'WRAP', 'PAPER', 'ENVELOPE', 'STICKER', 'NOTEBOOK']):
        return 'Stationery & Cards'
    if any(k in desc for k in ['FRAME', 'CLOCK', 'SIGN', 'PLAQUE', 'WALL', 'MIRROR']):
        return 'Home Decor'
    if any(k in desc for k in ['CHILDREN', 'CHILD', 'BABY', 'TOY', 'GAME', 'DOLL']):
        return 'Children & Toys'
    if any(k in desc for k in ['CHRISTMAS', 'XMAS', 'EASTER', 'HALLOWEEN', 'HOLIDAY']):
        return 'Seasonal & Gifts'
    if any(k in desc for k in ['FLOWER', 'PLANT', 'GARDEN', 'BOTANICAL', 'ROSE']):
        return 'Garden & Floral'
    if any(k in desc for k in ['CHARM', 'BRACELET', 'NECKLACE', 'EARRING', 'JEWEL']):
        return 'Jewelry & Accessories'
    
    # default category for items that dont match any of the above keywords
    # necessary to prevent null values in the product category dimension which could cause issues with joins and analysis later on
    return 'General Giftware'

# customer segmentation function
# cutoffs are set in accordance to stakeholders
# business rules encoding
def segment_customer(total_spend: float) -> str:
    if total_spend >= 5000:
        return 'VIP'
    if total_spend >= 1000:
        return 'High Value'
    if total_spend >= 200:
        return 'Mid Value'
    return 'Low Value'

# dimension builder functions
# build dim_country
def build_dim_country(df: pd.DataFrame) -> pd.DataFrame:
    # log
    logger.info('Building dim_country dimension')

    # create country dimension by extracting unique country names from the main dataframe
    dim_country = (
        # specify column
        # double bracket notation to ensure we get a DataFrame back instead of a Series which allows us to use DataFrame methods like drop_duplicates and rename
        df[['Country']]
        # deduplication
        .drop_duplicates()
        # schema alignment
        .rename(columns={'Country': 'country_name'})
        .sort_values('country_name')
        .reset_index(drop=True)
    )

    # assign regions based on the country name using the predefined REGION_MAP
    dim_country['region'] = dim_country['country_name'].map(REGION_MAP).fillna('Other')

    # log the number of rows in the dimension for debugging and validation purposes
    logger.info('Built dim_country with %d rows', len(dim_country))
    return dim_country

# build dim_product
def build_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    # log
    logger.info('Building dim_product dimension')

    # create product dimension by extracting unique product descriptions from the main dataframe
    dim_product = (
        # specify column
        df[['StockCode','Description']]
        # deduplication
        # using StockCode as the unique identifier for products instead of Description because descriptions can be inconsistent and may have duplicates, while StockCode is a more reliable unique key for products
        # avoiding dirty dimension with inconsistent descriptions and ensuring that each product is represented by a single record in the dimension table, which is crucial for accurate joins and analysis later on
        .drop_duplicates(subset=['StockCode'])
        # schema alignment
        .rename(columns={'Description': 'description',
                         'StockCode': 'stock_code'})
        .sort_values('stock_code')
        .reset_index(drop=True)
    )

    # assign categories to products based on their description using the categorize_product function
    # row level transformation to create a new column 'product_category' by applying the categorize_product function to each product description
    # .apply is pandas method that allows us to apply a function to each element in a Series (in this case, the 'description' column) and create a new column with the results
    dim_product['product_category'] = dim_product['description'].apply(categorize_product)

    # log the number of rows in the dimension for debugging and validation purposes
    logger.info('Built dim_product with %d rows', len(dim_product))
    return dim_product

# build dim_customer
# contains 3 group by attributes - first purchase date, primary country, total spend
def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    # log
    logger.info('Building dim_customer dimension')

    # get first purchase date
    # .min will give us the earliest invoice date for each customer
    first_purchase = (
        df.groupby('CustomerID')['InvoiceDate']
        .min()
        .reset_index()
        .rename(columns={'InvoiceDate': 'first_purchase_date'})
    )

    # primary country per customer
    # find the most frequent value; mode aggregation
    # may be data entry consistency inrelation to customerid and country of purchase
    # group, .size() to count occurrences, create count column, sort by descending, drop duplicates so it only keeps the msot frequent count which is the point of descending order, drop count column, rename for schema alignment
    primary_country = (
        df.groupby(['CustomerID', 'Country'])
        .size()
        .reset_index(name='count')
        .sort_values('count', ascending=False)
        .drop_duplicates(subset=['CustomerID'])
        .drop(columns=['count'])
        .rename(columns={'Country': 'country'})
    )

    # total amount spent
    total_spend = (
        df.groupby('CustomerID')['total_amount']
        .sum()
        .reset_index()
        .rename(columns={'total_amount': 'total_spend'})
    )

    # merge all customer attributes into a single dimension table
    # denormalized dimension to avoid the need for multiple joins when analyzing customer behavior, which can improve query performance and simplify analysis later on
    dim_customer = (
        first_purchase
        .merge(primary_country, on="CustomerID")
        .merge(total_spend, on='CustomerID')
        .rename(columns={'CustomerID': 'customer_id'})
    )

    dim_customer['customer_segment'] = dim_customer['total_spend'].apply(segment_customer)
    dim_customer = dim_customer.drop(columns=['total_spend'])

    logger.info('dim_customer built: %d rows', len(dim_customer))
    return dim_customer

# build dim_date
# create a date dimension that covers every date in the dataset, which allows for more flexible and efficient time-based analysis 
def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    # log
    logger.info('Building dim_date...')

    # Get full continuous date range
    # .normalize date to return date without time
    min_date = pd.to_datetime(df['InvoiceDate']).dt.normalize().min()
    max_date = pd.to_datetime(df['InvoiceDate']).dt.normalize().max()
    # generate everys single day between min and max dates for analysis
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')

    # derive date attributes from the full date range
    dim_date = pd.DataFrame({'full_date': date_range})

    # Smart key - YYYYMMDD format as integer
    dim_date['date_key']     = dim_date['full_date'].dt.strftime('%Y%m%d').astype(int)

    dim_date['year']        = dim_date['full_date'].dt.year
    dim_date['quarter']     = dim_date['full_date'].dt.quarter
    dim_date['month']       = dim_date['full_date'].dt.month
    dim_date['month_name']  = dim_date['full_date'].dt.strftime('%B')
    
    # .iso follows international standard for week numbering where the first week of the year is the one that contains the first Thursday of the year
    # .astype to handle .iso return of UInt32 type which can cause issues with some databases that expect standard integer types
    dim_date['week']        = dim_date['full_date'].dt.isocalendar().week.astype(int)
    
    dim_date['day_of_month'] = dim_date['full_date'].dt.day
    dim_date['day_of_week']  = dim_date['full_date'].dt.dayofweek    # 0=Monday, 6=Sunday
    dim_date['day_name']     = dim_date['full_date'].dt.strftime('%A')

    # Flags
    dim_date['is_weekend']   = dim_date['full_date'].dt.dayofweek >= 5
    dim_date['is_holiday']   = False

    logger.info('dim_date built: %d rows', len(dim_date))
    return dim_date

# load dimension function
def load_dimension(df: pd.DataFrame, table_name: str, db: DatabaseManager) -> None:
    # truncate table, enfrocing idempotency
    truncate_table(db, table_name)
    # create SQLAlchemy engine object
    # dg.get_engine helps with connection pooling
    engine = db.get_engine()
    # insert DF using pandas
    df.to_sql(table_name, engine, if_exists='append', index=False)

    # log
    logger.info('Loaded %d rows into %s', len(df), table_name)

# validate dimensions loaded
# post-load validation
def validate_dimension_counts(db: DatabaseManager) -> None:
    # log
    logger.info('Dimension row count:')

    # for loop for every dimension
    # query to count rows in each dimension table
    for table in ['dim_country', 'dim_product', 'dim_customer', 'dim_date']:
        # read_sql returns a DataFrame, we extract the count value from the first row and first column of the result to log the number of rows in each dimension table for validation purposes. 
        result = db.read_sql(f'SELECT COUNT(*) AS cnt FROM {table}')
        # if result is not None and has at least one row and one column, we extract the count value; otherwise, we log 'ERROR' to indicate that there was an issue with the query or the database connection. This helps with debugging and ensures that we have visibility into the success of our dimension loading process.
        count = result.iloc[0, 0] if result is not None else 'ERROR'
        logger.info('%-20s %s rows', table, count)

# main function to orchestrate the dimension loading process
def main(): 
    # log
    logger.info('Loading dimensions')

    # initialize database manager
    db = None

    # try catch block
    try: 
        # load cleaned data
        # fail fast approach to catch issues with file paths or data loading early on in the process. This ensures that we have the necessary data available before we attempt to build and load our dimensions, which can save time and resources if there are issues with the data.
        # read the csv file into memory before interacting with db
        logger.info('Loading cleaned data from: %s', CLEANED_DATA_PATH)
        df = pd.read_csv(CLEANED_DATA_PATH, parse_dates=['InvoiceDate'])
        logger.info('Loaded %d rows', len(df))

        # connect to database
        # load .env credentials
        db = DatabaseManager()
        db.connect()
       
        # build dimension dataframes
        # build dims in memory before loading
        # atomicity, either it all succeeds or nothing changes
        dim_country  = build_dim_country(df)
        dim_product  = build_dim_product(df)
        dim_customer = build_dim_customer(df)
        dim_date     = build_dim_date(df)

        # load dimensions into database
        # good practice to load dimensions by complexity starting with least complex
        load_dimension(dim_country,  'dim_country',  db)
        load_dimension(dim_product,  'dim_product',  db)
        load_dimension(dim_customer, 'dim_customer', db)
        load_dimension(dim_date,     'dim_date',     db)

        # validate
        validate_dimension_counts(db)

        # log completion
        logger.info('Dimension loading complete')


    except Exception as e:
        logger.error('Dimensioon load failed: %s', e, exc_info=True)
        raise

    finally:
        # close to avoid exhausting connection pool and to ensure that we clean up resources properly even if there is an error during the dimension loading process. This is important for maintaining the stability and performance.
        db.disconnect()

if __name__ == "__main__":
    main()