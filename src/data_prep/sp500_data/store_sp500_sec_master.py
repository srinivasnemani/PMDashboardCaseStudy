import sqlite3

import pandas as pd

SQLITE_DB = "sp500_data.db"
TABLE_NAME = "sp500_sec_master"
CSV_FILE = "sp500_security_info.csv"


def create_sec_master_table(db_file: str, table_name: str):
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        symbol VARCHAR(20),
        security VARCHAR(50),
        gics_sector VARCHAR(50),
        gics_sub_industry VARCHAR(50),
        cik INT,
        ff12industry VARCHAR(50)
    );
    """
    with sqlite3.connect(db_file) as conn:
        conn.execute(create_table_sql)
        conn.commit()


def load_and_store_sec_master(csv_file: str, db_file: str, table_name: str):
    df = pd.read_csv(csv_file, sep=",")
    df.rename(
        columns={
            "Symbol": "symbol",
            "Security": "security",
            "GICS Sector": "gics_sector",
            "GICS Sub-Industry": "gics_sub_industry",
            "CIK": "cik",
            "FF12Industry": "ff12industry",
        },
        inplace=True,
    )
    with sqlite3.connect(db_file) as conn:
        df.to_sql(table_name, conn, if_exists="append", index=False)


if __name__ == "__main__":
    # create_sec_master_table(SQLITE_DB, TABLE_NAME)
    load_and_store_sec_master(CSV_FILE, SQLITE_DB, TABLE_NAME)
