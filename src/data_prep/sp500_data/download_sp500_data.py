import time

import pandas as pd
import yfinance as yf


# Step 1: Get the list of S&P 500 companies
def get_sp500_constituents():
    # Method 1: Using pandas_datareader (may not always be up-to-date)
    try:
        import pandas_datareader as pdr

        tickers = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]
        return tickers["Symbol"].tolist()
    except:
        # Method 2: Direct Wikipedia scraping as backup
        tickers = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]
        return tickers["Symbol"].tolist()


# Step 2: Download price data for all constituents
def download_sp500_data(start_date, end_date, output_file):
    # Get S&P 500 constituents
    constituents = get_sp500_constituents()

    # Fix ticker symbols that use dots instead of hyphens
    constituents = [ticker.replace(".", "-") for ticker in constituents]
    print(f"Downloading data for {len(constituents)} companies...")

    # Create an empty DataFrame to store all close prices
    all_close_prices = pd.DataFrame()

    for i, ticker in enumerate(constituents):
        try:
            # Print progress
            if i % 50 == 0:
                print(f"Processing {i}/{len(constituents)} stocks...")
            time.sleep(1)  # Dont stress the server, You will be blocked :-)
            stock_data = yf.download(
                ticker, start=start_date, end=end_date, progress=False
            )
            close_prices = stock_data["Close"]
            close_prices.name = ticker

            ticker_df = pd.DataFrame(close_prices)
            ticker_df.columns = [ticker]  # Rename column to ticker symbol

            ticker_df = pd.DataFrame(close_prices)
            ticker_df.columns = [ticker]  # Rename column to ticker symbol
            all_close_prices = pd.concat([all_close_prices, ticker_df], axis=1)

        except Exception as e:
            print(f"Error downloading {ticker}: {e}")

    # Save to CSV
    all_close_prices.to_csv(output_file)
    print(f"Data saved to {output_file}")
    return all_close_prices


# Set date range for 2024 only
start_date = "2023-09-01"
end_date = "2025-04-01"  # Fixed to end of 2024 calendar year

# Download data
sp500_data = download_sp500_data(
    start_date, end_date, "sp500_close_prices_2024_2025_AllData.csv"
)

# Print summary
print(f"Downloaded close prices for {sp500_data.shape[1]} unique companies")
print(f"Date range: {sp500_data.index.min()} to {sp500_data.index.max()}")
