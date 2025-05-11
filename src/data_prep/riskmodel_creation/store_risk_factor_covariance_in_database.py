import glob
import os
import sqlite3
from datetime import datetime

import pandas as pd

# Folder with pkl files and destination SQLite DB path
folder_path = r"/data_prep/riskmodel_creation/weekly_risk_models_2024"
sqlite_path = os.path.join(folder_path, "risk_model_data.sqlite")
sqlite_path = r"/dbs/sp500_data.db"

# Open connection once
conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS factor_covariance (
        date TEXT,
        factor_1 TEXT,
        factor_2 TEXT,
        covariance REAL,
        PRIMARY KEY (date, factor_1, factor_2)
    )
"""
)


# Helper to extract date from filename (optional fallback)
def infer_date_from_filename(filename):
    digits = "".join(filter(str.isdigit, os.path.basename(filename)))
    try:
        return datetime.strptime(digits, "%Y%m%d").date()
    except ValueError:
        return None


# Loop over all .pkl files
pkl_files = glob.glob(os.path.join(folder_path, "*.pkl"))

for file_path in pkl_files:
    try:
        print(f"Processing: {file_path}")
        data = pd.read_pickle(file_path)

        cov_df = data.get("factor_covariance", None)
        as_of_date = data.get("as_of_date", None)

        if cov_df is None:
            print(f"Warning: 'factor_covariance' missing in {file_path}")
            continue

        if as_of_date is None:
            as_of_date = infer_date_from_filename(file_path)
            if as_of_date is None:
                raise ValueError(f"No 'as_of_date' or inferrable date in {file_path}")
        else:
            as_of_date = pd.to_datetime(as_of_date).date()

        # Convert wide matrix to long format
        cov_long = cov_df.reset_index().melt(
            id_vars=cov_df.index.name or "index",
            var_name="factor_2",
            value_name="covariance",
        )
        cov_long.rename(
            columns={cov_df.index.name or "index": "factor_1"}, inplace=True
        )
        cov_long["date"] = as_of_date
        cov_long = cov_long[["date", "factor_1", "factor_2", "covariance"]]

        # Insert into SQLite DB
        insert_sql = """
            INSERT OR REPLACE INTO factor_covariance (date, factor_1, factor_2, covariance)
            VALUES (?, ?, ?, ?)
        """
        cursor.executemany(insert_sql, cov_long.values.tolist())
        conn.commit()

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

# Close DB connection
conn.close()
print(f"✅ All covariance matrices loaded into: {sqlite_path}")
