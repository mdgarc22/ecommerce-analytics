# Import dependencies
# OS for file management
import os
# Logging for structured logs
import logging
# Typing for type hints
from typing import Optional

# MySQL connector for direct DB connections
import mysql.connector
from mysql.connector import Error
# Pandas for DataFrame operations
import pandas as pd
# Dotenv for loading environment variables from .env file
from dotenv import load_dotenv
# SQLAlchemy for engine creation and pandas integration
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine



# Create logger
# Allows log level control (DEBUG, INFO, WARNING, ERROR)
# Format: timestamp - level - message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


# Exceptions for database errors
class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid"""
    pass

# DatabaseManager class
class DatabaseManager:
    # Initialization loads config and validates it
    def __init__(self) -> None:
        load_dotenv()

        # connection/engine initialized to None until connect/get_engine called
        self.connection: Optional[mysql.connector.MySQLConnection] = None
        self.engine: Optional[Engine] = None

        self._load_config()
        self._validate_config()

    # Private method to load config from environment variables
    def _load_config(self) -> None:
        self._config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE'),
            'port': int(os.getenv('MYSQL_PORT', 3306))
        }

        # Connection string derived from same config dict
        # Used by SQLAlchemy (requires URL format vs dict format)
        self._connection_string = (
            f"mysql+mysqlconnector://"
            f"{self._config['user']}:{self._config['password']}"
            f"@{self._config['host']}:{self._config['port']}"
            f"/{self._config['database']}"
        )

    # Private method to validate config - checks for required fields and logs success
    def _validate_config(self) -> None:
        required_fields = ['host', 'user', 'password', 'database']

        missing = [
            field for field in required_fields
            if not self._config.get(field)
        ]

        if missing:
            raise DatabaseConfigError(
                f"Missing required config fields: {missing}. "
                f"Check your .env file."
            )

        logger.info("Configuration loaded successfully")

    # Public method to connect to database - sets self.connection and logs success or raises error
    def connect(self) -> 'DatabaseManager':
        # try except block to handle connection errors
        try:
            self.connection = mysql.connector.connect(**self._config)

            logger.info(
                "Connected to MySQL %s | Database: %s",
                self.connection.server_info,  # ← Use property instead of method
                self._config['database']
            )

        except Error as e:
            self.connection = None
            raise DatabaseConnectionError(
                f"Failed to connect to MySQL: {e}"
            ) from e

        return self

    # Public method to disconnect from database - closes connection if exists and logs result
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("MySQL connection closed")
        else:
            logger.warning("No active connection to close")

    # Public method to get SQLAlchemy engine - creates engine if not exists, tests connection, and logs result. Raises error if creation fails.
    def get_engine(self) -> Optional[Engine]:
        if self.engine is not None:
            logger.debug("Reusing existing SQLAlchemy engine")
            return self.engine

        try:
            self.engine = create_engine(
                self._connection_string,
                pool_pre_ping=True  # Verify connection before use
            )

            # Test engine connection
            with self.engine.connect():
                logger.info("SQLAlchemy engine created successfully")

        except Exception as e:
            self.engine = None
            raise DatabaseConnectionError(
                f"Failed to create SQLAlchemy engine: {e}"
            ) from e

        return self.engine

    # Public method to execute raw SQL query - uses self.connection, executes query with optional parameters, and returns results as list of tuples. Logs success or error and raises error if no connection.
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[list]:
        if not self.connection:
            raise DatabaseConnectionError(
                "No active connection. Call connect() first."
            )

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()

            logger.debug("Query executed successfully: %s", query[:50])
            return results

        except Error as e:
            logger.error("Query failed: %s | Error: %s", query[:50], e)
            return None

    # Public method to read SQL query into DataFrame - uses self.get_engine() to get engine and pd.read_sql() to execute query and return DataFrame. Logs success or error and returns None if query fails.
    def read_sql(self, query: str) -> Optional[pd.DataFrame]:
        try:
            engine = self.get_engine()
            return pd.read_sql(query, engine)

        except Exception as e:
            logger.error("read_sql failed: %s", e)
            return None

    # Public method to show tables in database - uses execute_query to run "SHOW TABLES" and returns list of table names. Logs result and returns empty list if no tables found.
    def show_tables(self) -> list:
        results = self.execute_query("SHOW TABLES;")

        if not results:
            logger.warning("No tables found in database")
            return []

        tables = [row[0] for row in results]

        logger.info(
            "Tables in '%s': %s",
            self._config['database'],
            tables
        )

        return tables



#  Test File
if __name__ == "__main__":

    logger.info("Starting DatabaseManager tests")

    # Instantiate - loads and validates config
    db = DatabaseManager()

    # Connect to database
    db.connect()

    # Show all tables
    db.show_tables()

    # Get SQLAlchemy engine
    engine = db.get_engine()

    # Verify engine reuse (check logs for "Reusing existing")
    db.get_engine()

    # Read tables as DataFrame
    df = db.read_sql("SHOW TABLES;")
    logger.info("Tables as DataFrame:\n%s", df)

    # Disconnect
    db.disconnect()

    # Verify disconnected state
    db.disconnect()

    logger.info("All tests complete")