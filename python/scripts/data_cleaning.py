# Import dependencies
# logging for structured logs
import logging
# pathlib for file path management
from pathlib import Path
# typing for type hints
from typing import Tuple
# datetime for timestamping logs and reports
from datetime import datetime

# Pandas for DataFrame operations
import pandas as pd
# NumPy for numerical operations
import numpy as np

# Configure logging
# Allows log level control (DEBUG, INFO, WARNING, ERROR)
# Format: timestamp - level - message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create logger object
logger = logging.getLogger(__name__)

# File paths
#  Get project root directory (two levels up from current file)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# create immutable outputs; each run will generate a new file providing an audit trail of changes over time (data lineage)
# timestamp for report naming
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# Define paths for raw and cleaned data
RAW_DATA_PATH = PROJECT_ROOT / 'data' / 'raw' / 'online_retail.csv'
CLEANED_DATA_PATH = PROJECT_ROOT / 'data' / 'cleaned' / f'cleaned_data_{timestamp}.csv'
REPORT_PATH = PROJECT_ROOT / 'data' / 'processed' / 'cleaning_report.txt'

# Create processed directory if it doesn't exist
CLEANED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


# Data quality report class
class DataQualityReport:

    def __init__(self, initial_rows: int):
        self.initial_rows = initial_rows
        self.final_rows = 0
        # placeholder var's for metrics
        self.metrics = {
            'null_customer_id': 0,
            'cancelled_orders': 0,
            'invalid_quantity': 0,
            'invalid_price': 0,
            'duplicates': 0
          }
    
    # Update metrics method
    def update(self, metric_name: str, count: int) -> None:
        if metric_name in self.metrics:
            self.metrics[metric_name] = count
        else:
            logger.warning(f"Metric '{metric_name}' not found in report metrics.")

    # Final rows setter
    def set_final_rows(self, count: int) -> None:
        self.final_rows = count

    # Removed rows counter
    def removed_rows(self) -> int:
        return self.initial_rows - self.final_rows
        
    # Retention rate
    def retention_rate(self) -> float:
        return (self.final_rows / self.initial_rows * 100) if self.initial_rows > 0 else 0.0
    
    # Generate report string
    def generate_report(self) -> str:
        report = []
        report.append("-" * 40)
        report.append("Data Cleaning Report")
        report.append("-" * 40)
        report.append(f"\nInitial rows: {self.initial_rows:,}")
        report.append("\nRows removed by issue:")
        
        for issue, count in self.metrics.items():
            pct = (count / self.initial_rows) * 100
            report.append(f"  - {issue.replace('_', ' ').title()}: {count:,} ({pct:.2f}%)")
        
        report.append(f"\nTotal removed: {self.removed_rows():,}")
        report.append(f"Final rows: {self.final_rows:,}")
        report.append(f"Retention rate: {self.retention_rate():.2f}%")
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    

# Data Cleaning Functions
# Load raw data function
def load_raw_data(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")
    
    logger.info("Loading raw data from: %s", file_path)

    df = pd.read_csv(file_path, encoding='ISO-8859-1', parse_dates=['InvoiceDate'])

    logger.info("Raw data loaded with %d rows and %d columns", len(df), len(df.columns))
    
    return df

# Remove rows with null CustomerID
def remove_null_customers(df: pd.DataFrame, report: DataQualityReport) -> pd.DataFrame:
    # Initial length of DataFrame
    initial_count = len(df)

    # Keep rows where CustomerID is not null
    # .copy() to avoid SettingWithCopyWarning
    df_clean = df[df['CustomerID'].notna()].copy()

    # Count how many rows were removed
    removed = initial_count - len(df_clean)
    report.update('null_customer_id', removed)

    logger.info("Removed %s rows with null CustomerID (%.2f%%)", removed, (removed / initial_count) * 100)

    return df_clean

# Remove cancelled orders (Invoice starts with 'C')
def remove_cancelled_orders(df: pd.DataFrame, report: DataQualityReport) -> pd.DataFrame:
    # Initial length of DataFrame
    initial_count = len(df)

    # Keep rows where Invoice does not start with 'C'
    df_clean = df[~df['InvoiceNo'].astype(str).str.startswith('C')].copy()

    # Count how many rows were removed
    removed = initial_count - len(df_clean)
    report.update('cancelled_orders', removed)

    logger.info("Removed %s cancelled orders (%.2f%%)", removed, (removed / initial_count) * 100)

    return df_clean

# Remove rows with invalid Quantity
def remove_invalid_quantities(df: pd.DataFrame, report: DataQualityReport) -> pd.DataFrame:
    # Initial length of DataFrame
    initial_count = len(df)

    # Keep rows where Quantity column is positive
    df_clean = df[df['Quantity'] > 0].copy()

    # Count how many rows were removed
    removed = initial_count - len(df_clean)
    report.update('invalid_quantity', removed)

    logger.info("Removed %s rows with invalid Quantity (%.2f%%)", removed, (removed / initial_count) * 100)

    return df_clean

# Remove rows with invalid UnitPrice
def remove_invalid_prices(df: pd.DataFrame, report: DataQualityReport) -> pd.DataFrame:
    # Initial length of DataFrame
    initial_count = len(df)

    # Keep rows where UnitPrice column is positive
    df_clean = df[df['UnitPrice'] > 0].copy()

    # Count how many rows were removed
    removed = initial_count - len(df_clean)
    report.update('invalid_price', removed)

    logger.info("Removed %s rows with invalid UnitPrice (%.2f%%)", removed, (removed / initial_count) * 100)

    return df_clean

# Remove duplicate rows
def remove_duplicates(df: pd.DataFrame, report: DataQualityReport) -> pd.DataFrame:
    # Initial length of DataFrame
    initial_count = len(df)

    # Keep only unique rows
    df_clean = df.drop_duplicates().copy()

    # Count how many rows were removed
    removed = initial_count - len(df_clean)
    report.update('duplicates', removed)

    logger.info("Removed %s duplicate rows (%.2f%%)", removed, (removed / initial_count) * 100)

    return df_clean

# clean text fields (e.g. strip whitespace, standardize case)
def clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning text fields")

    # Strip whitepsaces and uppercase
    df['Description'] = df['Description'].str.strip().str.upper()

    df['StockCode'] = df['StockCode'].astype(str).str.upper()

    logger.info("Text fields cleaned")

    return df

# Create calculated fields
def create_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Creating calculated fields")

    # TotalPrice = Quantity * UnitPrice
    df['total_amount'] = df['Quantity'] * df['UnitPrice']

    df['is_return'] = False

    logger.info("Calculated fields created")

    return df

# Main cleaning function that runs all steps in sequence
def clean_data_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, DataQualityReport]:
    logger.info("Starting data cleaning pipeline")

    # Initialize quality tracking
    report = DataQualityReport(initial_rows=len(df))
    
    # Execute cleaning steps in sequence
    # Each function receives cleaned data from previous step
    df = remove_null_customers(df, report)
    df = remove_cancelled_orders(df, report)
    df = remove_invalid_quantities(df, report)
    df = remove_invalid_prices(df, report)
    df = remove_duplicates(df, report)
    df = clean_text_fields(df)
    df = create_calculated_fields(df)
    
    # Record final state
    report.set_final_rows(len(df))
    
    logger.info("Data cleaning pipeline complete")
    logger.info("Retention rate: %.2f%%", report.retention_rate())
    
    return df, report

def save_cleaned_data(df: pd.DataFrame, file_path: Path) -> None:
    logger.info("Saving cleaned data to: %s", file_path)
    df.to_csv(file_path, index=False, encoding='UTF-8')
    logger.info("Cleaned data saved: %s rows", len(df))

def save_report(report: DataQualityReport, file_path: Path) -> None:
    # Generate report text from the report object
    report_text = report.generate_report()
    
    logger.info("Saving cleaning report to: %s", file_path)
    
    # Write the report text to a file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    logger.info("Report saved")
    
    # Also print to console for immediate visibility
    print("\n" + report_text)

def main() -> None:
    logger.info("=" * 60)
    logger.info("DATA CLEANING SCRIPT")
    logger.info("=" * 60)
    
    try:
        # STEP 1: Load raw data (Extract)
        df_raw = load_raw_data(RAW_DATA_PATH)
        
        # STEP 2: Clean data (Transform)
        df_clean, report = clean_data_pipeline(df_raw)
        
        # STEP 3: Save outputs (Load to file, not DB yet)
        save_cleaned_data(df_clean, CLEANED_DATA_PATH)
        save_report(report, REPORT_PATH)
        
        logger.info("=" * 60)
        logger.info("DATA CLEANING COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        # Catch any errors and log them with full traceback
        logger.error("Data cleaning failed: %s", e, exc_info=True)
        raise


# This runs only when file is executed directly
# Not when imported as a module
if __name__ == "__main__":
    main()