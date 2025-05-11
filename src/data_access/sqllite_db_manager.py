import logging
from enum import Enum
from pathlib import Path
from typing import Optional

from sqlalchemy import (Column, Date, Float, Integer, MetaData, String, Table,
                        create_engine, text)
from sqlalchemy.engine import Engine

# Database path configuration
SQLLITE_DB_PATH = Path(r"C:\CaseStudy\dbs\sp500_data.db")
SQLLITE_DB_PATH = Path(__file__).parent.parent.parent / "dbs" / "sp500_data.db"
# SQLLITE_DB_PATH = Path(r"C:\CaseStudy\dbs\sp500_data_2test.db")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TableNames(Enum):
    """Enum for database table names"""

    TS_DATA = "sp500_ts_data"
    ALPHA_SCORES = "alpha_history"
    TRADE_BOOKING = "trade_booking"
    AUM_LEVERAGE = "aum_and_leverage"
    RISK_FACTOR_COVARIANCE = "factor_covariance"
    RISK_FACTOR_EXPOSURES = "factor_exposures"
    RISK_SPRISK_RESIDUALS = "sprisk_residuals"


class DatabaseManager:
    """Class to manage database operations and table creation"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the database manager with a database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path or SQLLITE_DB_PATH
        self.engine = create_engine(f"sqlite:///{self.db_path.as_posix()}")
        self.metadata = MetaData()
        logger.info(f"Database manager initialized with database at {self.db_path}")

    def get_engine(self) -> Engine:
        """
        Get the SQLAlchemy engine instance.

        Returns:
            SQLAlchemy engine
        """
        return self.engine

    def create_table(self, table_name: str, columns_dict: dict) -> bool:
        """
        Generic method to create a table using SQLAlchemy ORM.

        Args:
            table_name: Name of the table to create
            columns_dict: Dictionary of column definitions {column_name: column_type}

        Returns:
            bool: True if table was created successfully or already exists
        """
        try:
            table_columns = []
            for col_name, col_type in columns_dict.items():
                table_columns.append(Column(col_name, col_type))

            table = Table(table_name, self.metadata, *table_columns)

            # Create the table if it doesn't exist
            self.metadata.create_all(self.engine, tables=[table])
            logger.info(f"Table '{table_name}' successfully created or already exists")
            return True

        except Exception as e:
            logger.error(f"Error creating table '{table_name}': {str(e)}")
            return False

    def create_table_sql(self, table_name: str, create_sql: str) -> bool:
        """
        Create a table using raw SQL.

        Args:
            table_name: Name of the table to create
            create_sql: SQL statement to create the table

        Returns:
            bool: True if table was created successfully or already exists
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()

            logger.info(f"Table '{table_name}' created or already exists")
            return True

        except Exception as e:
            logger.error(f"Error creating table '{table_name}': {str(e)}")
            return False

    def create_alpha_table(self) -> bool:
        """
        Create the alpha history table.

        Returns:
            bool: True if table was created successfully or already exists
        """
        table_name = TableNames.ALPHA_SCORES.value
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            date TEXT,
            trade_direction TEXT,
            ticker TEXT,
            alpha_score REAL,
            weight REAL,
            strategy_name TEXT
        );
        """
        return self.create_table_sql(table_name, create_sql)

    def create_trade_booking_table(self) -> bool:
        """
        Create the trade booking table.

        Returns:
            bool: True if table was created successfully or already exists
        """
        try:
            table_name = TableNames.TRADE_BOOKING.value

            # Define columns
            columns = {
                "strategy": String,
                "trade_open_date": Date,
                "ticker": String,
                "shares": Integer,
                "trade_open_price": Float,
                "direction": String,
                "trade_close_date": Date,
                "trade_close_price": Float,
            }

            return self.create_table(table_name, columns)

        except Exception as e:
            logger.error(f"Error creating trade booking table: {str(e)}")
            return False

    def create_aum_leverage_table(self) -> bool:
        """
        Create the AUM and leverage table.

        Returns:
            bool: True if table was created successfully or already exists
        """
        try:
            table_name = TableNames.AUM_LEVERAGE.value

            # Define columns
            columns = {
                "date": String,
                "strategy_name": String,
                "aum": Float,
                "target_leverage": Float,
            }

            return self.create_table(table_name, columns)

        except Exception as e:
            logger.error(f"Error creating AUM and leverage table: {str(e)}")
            return False


# Utility function for backward compatibility
def get_db_engine() -> Engine:
    """
    Get the default database engine.

    Returns:
        SQLAlchemy engine
    """
    db_manager = DatabaseManager()
    return db_manager.get_engine()


# Example usage
if __name__ == "__main__":
    db_manager = DatabaseManager()

    # Create tables
    alpha_success = db_manager.create_alpha_table()
    # trade_success = db_manager.create_trade_booking_table()
    success_flag = db_manager.create_aum_leverage_table()

    print(f"Alpha table created: {success_flag}")
