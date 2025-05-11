import pandas as pd
import yfinance as yf

from data_prep.sp500_data.store_sp500_ts_data import store_sp500_index_price

store_sp500_index_price()

# Set date range
start_date = "2023-09-01"
end_date = "2025-03-31"

# Download S&P 500 Index (^GSPC)
data = yf.Ticker("^GSPC").history(start=start_date, end=end_date)

# Extract 'Close' price
sp500_close = data["Close"].copy()
sp500_close.name = "S&P500_Close"

# Remove timezone
sp500_close.index = sp500_close.index.tz_localize(None)

# Create full weekday index
business_days = pd.date_range(start=start_date, end=end_date, freq="B")

# Reindex, fill missing prices
sp500_close = sp500_close.reindex(business_days)
sp500_close = sp500_close.ffill().bfill()

# Save to CSV
sp500_close.to_csv("sp500_index_price_2023-09-01_to_2025-03-31.csv")
print("S&P 500 index price CSV saved successfully.")
