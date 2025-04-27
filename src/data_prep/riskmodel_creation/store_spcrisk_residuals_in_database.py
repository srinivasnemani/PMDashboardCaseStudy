import glob
import os
import sqlite3
from datetime import datetime

import pandas as pd

# Folder and database path
folder_path = r"/data_prep/riskmodel_creation/weekly_risk_models_2024"
sqlite_path = os.path.join(folder_path, "risk_model_data.sqlite")
sqlite_path = r"/dbs/sp500_data.db"

# Connect to SQLite DB
conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sprisk_residuals (
        date TEXT,
        ticker TEXT,
        specific_risk REAL,
        residual REAL,
        PRIMARY KEY (date, ticker)
    )
""")

# Optional: helper to infer date from filename
def infer_date_from_filename(filename):
    digits = ''.join(filter(str.isdigit, os.path.basename(filename)))
    try:
        return datetime.strptime(digits, "%Y%m%d").date()
    except ValueError:
        return None

# Process all .pkl files
pkl_files = glob.glob(os.path.join(folder_path, "*.pkl"))

for file_path in pkl_files:
    try:
        print(f"📦 Processing: {file_path}")
        data = pd.read_pickle(file_path)

        # Extract as_of_date
        as_of_date = data.get("as_of_date", None)
        if as_of_date is None:
            as_of_date = infer_date_from_filename(file_path)
            if as_of_date is None:
                raise ValueError(f"Date missing or unparseable for file: {file_path}")
        else:
            as_of_date = pd.to_datetime(as_of_date).date()

        # Extract data
        specific_risk = data.get("specific_risk")
        residuals = data.get("residuals")

        if specific_risk is None or residuals is None:
            print(f"⚠️ Skipping: missing 'specific_risk' or 'residuals' in {file_path}")
            continue

        # Transform to DataFrame with ticker as index
        sr_df = specific_risk.to_frame(name='specific_risk')
        res_df = residuals.T
        res_df.columns = ['residual']# Ticker as index
        # if as_of_date not in residuals.index:
        #     raise ValueError(f"Residuals do not have entry for as_of_date: {as_of_date}")

        # Get residuals for the date and join
        # res_row = res_df[[as_of_date]].rename(columns={as_of_date: 'residual'})
        merged = sr_df.join(res_df, how='inner').reset_index()
        merged['date'] = as_of_date
        merged = merged[['date', 'Ticker', 'specific_risk', 'residual']]
        merged.columns = ['date', 'ticker', 'specific_risk', 'residual']

        # Insert into SQLite
        insert_sql = """
            INSERT OR REPLACE INTO sprisk_residuals (date, ticker, specific_risk, residual)
            VALUES (?, ?, ?, ?)
        """
        cursor.executemany(insert_sql, merged.values.tolist())
        conn.commit()

    except Exception as e:
        print(f"❌ Error in {file_path}: {e}")

# Finalize
conn.close()
print(f"\n✅ Finished loading all specific risk and residuals into: {sqlite_path}")
