import sqlite3

import pandas as pd

SQLITE_DB = r"C:\CaseStudy\dbs\sp500_data.db"
SECURITY_TS_DATA = "sp500_ts_data"


def create_security_ts_table(db_file: str, table_name: str):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        date DATE,
        ticker VARCHAR(25),
        key VARCHAR(30),
        value REAL
    );
    """
    with sqlite3.connect(db_file) as conn:
        conn.execute(create_table_sql)
        conn.commit()


def transform_csv_to_long_format(csv_file: str, key: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
    df.index.name = "date"
    long_df = df.reset_index().melt(
        id_vars=["date"], var_name="ticker", value_name="value"
    )
    long_df["key"] = key
    return long_df[["date", "ticker", "key", "value"]]


def store_dataframe_in_db(
    df: pd.DataFrame, db_file: str, table_name: str, mode: str = "replace"
):
    with sqlite3.connect(db_file) as conn:
        df.to_sql(table_name, conn, if_exists=mode, index=False)


def store_benchmark_constituents_weights_in_db():
    csv_file = "sp500_estimated_weights_2024-09-01_to_2025-03-31.csv"
    df_long = transform_csv_to_long_format(csv_file, key="wgt_in_benchmark")
    store_dataframe_in_db(df_long, SQLITE_DB, SECURITY_TS_DATA, mode="append")


def store_prices_in_db():
    csv_file = "sp500_close_prices_2024_2025_AllData.csv"
    df_long = transform_csv_to_long_format(csv_file, key="px_last")
    store_dataframe_in_db(df_long, SQLITE_DB, SECURITY_TS_DATA, mode="append")


def store_mcaps_in_db():
    csv_file = "sp500_market_caps_usd.csv"
    df_long = transform_csv_to_long_format(csv_file, key="mcap")
    store_dataframe_in_db(df_long, SQLITE_DB, SECURITY_TS_DATA, mode="append")


def store_sp500_index_price():
    csv_file_index = "sp500_index_price_2023-09-01_to_2025-03-31.csv"
    df_index = pd.read_csv(csv_file_index, index_col=0, parse_dates=True)
    df_index.index.name = "date"
    df_index.columns = ["value"]
    df_index = df_index.reset_index()
    df_index["ticker"] = "SP500"
    df_index["key"] = "px_last"
    df_index = df_index[["date", "ticker", "key", "value"]]
    store_dataframe_in_db(df_index, SQLITE_DB, SECURITY_TS_DATA, mode="append")


if __name__ == "__main__":
    # create_security_ts_table(SQLITE_DB, SECURITY_TS_DATA)
    # store_benchmark_constituents_weights_in_db()
    # store_prices_in_db()
    store_sp500_index_price()
    # store_mcaps_in_db()
