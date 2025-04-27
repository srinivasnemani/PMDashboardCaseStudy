import glob
import os
import sqlite3
from datetime import datetime

import pandas as pd

# Path to the folder containing all the pickle files
folder_path = r"/data_prep/riskmodel_creation/weekly_risk_models_2024"
sqlite_path = os.path.join(folder_path, "risk_model_data.sqlite")
sqlite_path = r"/dbs/sp500_data.db"

# Connect to SQLite DB (create if doesn't exist)
conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS industry_exposure (
        date TEXT,
        ticker TEXT,
        factor TEXT,
        exposure REAL,
        PRIMARY KEY (date, ticker, factor)
    )
""")


# Helper to infer date from filename if needed
def infer_date_from_filename(filename):
    digits = ''.join(filter(str.isdigit, os.path.basename(filename)))
    try:
        return datetime.strptime(digits, "%Y%m%d").date()
    except ValueError:
        return None


# Process each .pkl file in the folder
pkl_files = glob.glob(os.path.join(folder_path, "*.pkl"))

for file_path in pkl_files:
    try:
        print(f"Processing: {file_path}")
        data = pd.read_pickle(file_path)

        # Extract industry exposures
        df = data.get("industry_exposures", None)
        if df is None:
            print(f"Warning: 'industry_exposures' not found in {file_path}")
            continue

        # Get or infer as_of_date
        as_of_date = data.get('as_of_date', None)
        if as_of_date is None:
            as_of_date = infer_date_from_filename(file_path)
            if as_of_date is None:
                raise ValueError(f"Missing as_of_date in both data and filename for {file_path}")
        else:
            as_of_date = pd.to_datetime(as_of_date).date()

        # Reshape and insert
        df = df.reset_index().melt(id_vars='Ticker', var_name='factor', value_name='exposure')
        df['date'] = as_of_date
        df = df[['date', 'Ticker', 'factor', 'exposure']]
        df.columns = ['date', 'ticker', 'factor', 'exposure']

        # Insert into SQLite (replace on conflict)
        insert_sql = """
            INSERT OR REPLACE INTO factor_exposure (date, ticker, factor, exposure)
            VALUES (?, ?, ?, ?)
        """
        cursor.executemany(insert_sql, df.values.tolist())
        conn.commit()

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

conn.close()
print(f"✅ All pickle files processed and stored in: {sqlite_path}")
