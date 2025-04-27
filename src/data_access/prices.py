import logging

import pandas as pd
from src.data_access.crud_util import DataAccessUtil
from src.data_access.schemas import UniverseSpec
from src.data_access.sqllite_db_manager import TableNames, get_db_engine
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PriceDataFetcher:
    """Class for fetching price and benchmark data from the database using static methods."""

    @staticmethod
    def get_price_data(spec: UniverseSpec, engine=None) -> pd.DataFrame:
        """
        Fetch price data (excluding benchmark indices) based on the given specification.

        Args:
            spec: Universe specification with date ranges
            engine: SQLAlchemy database engine (optional, will use default if None)

        Returns:
            DataFrame with date, ticker, and value columns
        """
        if engine is None:
            engine = get_db_engine()

        return PriceDataFetcher._fetch_data(
            spec=spec,
            engine=engine,
            ticker_condition="ticker NOT IN ('SP500')"
        )

    @staticmethod
    def get_benchmark_data(spec: UniverseSpec, engine=None) -> pd.DataFrame:
        """
        Fetch benchmark data (SP500) based on the given specification.

        Args:
            spec: Universe specification with date ranges
            engine: SQLAlchemy database engine (optional, will use default if None)

        Returns:
            DataFrame with date, ticker, and value columns
        """
        if engine is None:
            engine = get_db_engine()

        return PriceDataFetcher._fetch_data(
            spec=spec,
            engine=engine,
            ticker_condition="ticker IN ('SP500')"
        )

    @staticmethod
    def _fetch_data(spec: UniverseSpec, engine, ticker_condition: str) -> pd.DataFrame:
        """
        Internal method to fetch data based on ticker condition.

        Args:
            spec: Universe specification with date ranges
            engine: SQLAlchemy database engine
            ticker_condition: SQL condition for filtering tickers

        Returns:
            DataFrame with date, ticker, and value columns
        """
        table_name = TableNames.TS_DATA.value

        # Build SQL query
        base_query = f"""
        SELECT date, ticker, value
        FROM {table_name}
        WHERE key = 'px_last'
          AND {ticker_condition}
        """

        params = {}
        conditions = []

        # Apply date conditions using SQLite's date() function
        if spec.start_date:
            conditions.append("date(date) >= date(:start_date)")
            params["start_date"] = spec.start_date
        if spec.end_date:
            conditions.append("date(date) <= date(:end_date)")
            params["end_date"] = spec.end_date

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        stmt = text(base_query)
        df = DataAccessUtil.fetch_data_from_db(stmt, params)
        return df

    @staticmethod
    def get_ticker_prices(tickers_list, query_date):
        """
        Fetch price data for unique tickers in trade_data on the rebalance date

        Parameters:
        tickers_list: unique_tickers_list (np array)
        query_date (datetime or str): Date for which to retrieve prices

        Returns:
        DataFrame: Price data for the tickers on the specified date
        """
        table_name = TableNames.TS_DATA.value

        # Convert tickers to a comma-separated string with quotes
        tickers_str = "'" + "','".join(tickers_list) + "'"

        # Use the string directly in the query
        base_query = f"""
        SELECT ticker, value 
        FROM {table_name}
        WHERE key = 'px_last' 
        AND date(date) = date(:query_date)
        AND ticker IN ({tickers_str})
        """

        # Initialize parameters dictionary (only for query_date)
        params = {
            "query_date": pd.Timestamp(query_date).date().isoformat()
        }

        # No additional conditions for this specific use case
        conditions = []

        # Append conditions to the base query if needed
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Convert to SQLAlchemy text object
        stmt = text(base_query)

        # Execute query and return results
        db_engine = get_db_engine()

        # Use your existing DataAccessUtil if compatible with text() objects
        # Otherwise, execute directly:
        with db_engine.connect() as connection:
            result = connection.execute(stmt, params)
            df_prices = pd.DataFrame(result.fetchall(), columns=result.keys())

        # Log information about the result
        if not df_prices.empty:
            logger.info(f"Retrieved prices for {len(df_prices)} tickers on {query_date}")
        else:
            logger.warning(f"No price data found for tickers on {query_date}")

        return df_prices



if __name__ == "__main__":
    spec = UniverseSpec(start_date="2024-01-01", end_date="2024-12-31")

    # Using the static methods directly
    price_df = PriceDataFetcher.get_price_data(spec)
    print(price_df['date'].unique())

    benchmark_df = PriceDataFetcher.get_benchmark_data(spec)
    print(f"Benchmark tickers: {benchmark_df['ticker'].unique()}")

    # Or using the compatibility functions
    # price_df = fetch_price_data(spec)
    # print(price_df['date'].unique())
