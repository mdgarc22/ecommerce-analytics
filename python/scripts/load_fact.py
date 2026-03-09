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
    logger.info('Loafin dimension lookup tables')

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