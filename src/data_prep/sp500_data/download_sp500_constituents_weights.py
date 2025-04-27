import pandas as pd
import yfinance as yf

# Parameters
start_date = "2023-09-01"
end_date = "2025-03-31"

# Get S&P 500 tickers from Wikipedia
sp500_table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
tickers = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()

# Dictionary to collect per-ticker market caps
all_market_caps = {}

# Loop through tickers
for ticker in tickers:
    try:
        # Download price data
        # time.sleep(0.5)
        data = yf.Ticker(ticker).history(start=start_date, end=end_date)
        shares_outstanding = yf.Ticker(ticker).info.get('sharesOutstanding', None)

        if shares_outstanding and not data.empty:
            data = data[['Close']].rename(columns={'Close': ticker})
            data[ticker] = data[ticker] * shares_outstanding  # Approximate Market Cap
            all_market_caps[ticker] = data[ticker]
    except Exception as e:
        print(f"Failed for {ticker}: {e}")

# Combine into raw market cap frame
market_caps_df_raw = pd.DataFrame(all_market_caps)

# Drop timezone (make tz-naive)
market_caps_df_raw.index = market_caps_df_raw.index.tz_localize(None)

# Create full weekday index (tz-naive by default)
full_weekdays = pd.date_range(start=start_date, end=end_date, freq='B')

# Create target frame and join
market_caps_df = pd.DataFrame(index=full_weekdays)
market_caps_df = market_caps_df.join(market_caps_df_raw)

# Drop all-NaN columns (stocks with zero data)
market_caps_df.dropna(axis=1, how='all', inplace=True)

# Forward then backward fill
market_caps_df = market_caps_df.ffill().bfill()

# Compute daily weights
weights_df = market_caps_df.div(market_caps_df.sum(axis=1), axis=0)

# Save to CSV
weights_df.to_csv("sp500_estimated_weights_2024-09-01_to_2025-03-31.csv")
print("CSV with forward-filled weekday weights saved successfully.")
