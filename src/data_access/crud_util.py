import logging

import pandas as pd

from src.data_access.sqllite_db_manager import get_db_engine

# Configure logging
logger = logging.getLogger(__name__)


class DataAccessUtil:

    @staticmethod
    def fetch_data_from_db(sql_query, params=None, engine=None):
        # Execute the query
        if engine is None:
            engine = get_db_engine()

        with engine.connect() as conn:
            result = conn.execute(sql_query) if params is None else conn.execute(sql_query, params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        if not df.empty and ('date' in df.columns):
            df['date'] = pd.to_datetime(df['date'])
            logger.info(f"Date range in result: {df['date'].min()} to {df['date'].max()}")
            logger.info(f"Total rows: {len(df)}")
        else:
            logger.warning("Query returned no results")

        return df

    @staticmethod
    def store_dataframe_to_table(dataframe, table_name, if_exists='append', index=False, engine=None):
        """
        Stores a pandas DataFrame to a database table.

        Args:
            engine: SQLAlchemy database engine
            dataframe: pandas DataFrame to store
            table_name: Name of the target table
            if_exists: How to behave if the table exists ('fail', 'replace', or 'append')
            index: Whether to store the DataFrame index as a column

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if engine is None:
                engine = get_db_engine()

            dataframe.to_sql(
                name=table_name,
                con=engine,
                if_exists=if_exists,
                index=index,
                chunksize=100_000
            )
            logger.info(f"Successfully stored {len(dataframe)} rows to table '{table_name}'")
            return True
        except Exception as e:
            logger.error(f"Error storing DataFrame to table '{table_name}': {str(e)}")
            return False
