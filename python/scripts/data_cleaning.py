# Import dependencies
# logging for structured logs
import logging
# pathlib for file path management
from pathlib import Path
# typing for type hints
from typing import Tuple

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

# Define paths for raw and cleaned data
RAW_DATA_PATH = PROJECT_ROOT / 'data' / 'raw' / 'online_retail.csv'
CLEANED_DATA_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'cleaned_data.csv'
REPORT_PATH = PROJECT_ROOT / 'data' / 'processed' / 'cleaning_report.txt'

# Create processed directory if it doesn't exist
CLEANED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


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
        
        report.append(f"\nTotal removed: {self.total_removed():,}")
        report.append(f"Final rows: {self.final_rows:,}")
        report.append(f"Retention rate: {self.retention_rate():.2f}%")
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    

    # Data Cleaning Functions
    # Load raw data function
    
