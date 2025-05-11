import os
import time

import pandas as pd
import yfinance as yf


# Get S&P 500 company information
def get_sp500_info():
    try:
        # Read the Wikipedia table
        sp500_info = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]

        # Select only the required columns
        sp500_info = sp500_info[
            ["Symbol", "Security", "GICS Sector", "GICS Sub-Industry", "CIK"]
        ]

        # Fix ticker symbols that use dots instead of hyphens
        sp500_info["Symbol"] = sp500_info["Symbol"].str.replace(".", "-")

        return sp500_info
    except Exception as e:
        print(f"Error getting S&P 500 information: {e}")
        return None


# Get daily market cap data for all S&P 500 constituents
def get_daily_market_caps(start_date, end_date, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get S&P 500 information
    sp500_info = get_sp500_info()

    if sp500_info is None:
        return None

    print(f"Retrieved information for {len(sp500_info)} companies")
    tickers = sp500_info["Symbol"].tolist()

    # Save security info to CSV
    sp500_info.to_csv(f"{output_dir}/sp500_security_info.csv", index=False)
    print(f"Security info saved to {output_dir}/sp500_security_info.csv")

    # DataFrame to store all market cap data
    all_market_caps = pd.DataFrame()

    # Get market cap data for each company
    for i, ticker in enumerate(tickers):
        time.sleep(1)
        try:
            # Print progress
            if i % 20 == 0:
                print(f"Processing {i}/{len(tickers)}: {ticker}")

            # Get stock info from Yahoo Finance
            stock = yf.Ticker(ticker)

            # Get historical price data
            hist = stock.history(start=start_date, end=end_date)

            if not hist.empty:
                # Get shares outstanding
                try:
                    shares = stock.info.get("sharesOutstanding", None)

                    if shares:
                        # Calculate daily market cap (shares * daily close price)
                        market_cap = hist["Close"] * shares
                        market_cap.name = ticker

                        if all_market_caps.empty:
                            all_market_caps = pd.DataFrame(market_cap, columns=[ticker])
                        else:
                            new_data = pd.DataFrame(market_cap, columns=[ticker])
                            all_market_caps = pd.concat(
                                [all_market_caps, new_data], axis=1
                            )

                except Exception as e:
                    print(f"Error calculating market cap for {ticker}: {e}")

            # Add delay to avoid hitting API rate limits
            time.sleep(0.1)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    # Save to CSV files
    if not all_market_caps.empty:
        print(f"Saving market cap data for {all_market_caps.shape[1]} companies...")

        # Save raw market cap data
        all_market_caps.to_csv(f"{output_dir}/sp500_market_caps_usd.csv")
        print(f"Raw market cap data saved to {output_dir}/sp500_market_caps_usd.csv")

        # Convert to billions for readability and save
        market_caps_billions = all_market_caps / 1_000_000_000
        market_caps_billions.to_csv(f"{output_dir}/sp500_market_caps_billions_usd.csv")
        print(
            f"Market cap data in billions saved to {output_dir}/sp500_market_caps_billions_usd.csv"
        )

        return all_market_caps

    return None


# Set date range
start_date = "2023-09-01"
end_date = "2025-03-31"

# Get and save daily market cap data to CSV files
output_directory = "sp500_data"
market_caps = get_daily_market_caps(start_date, end_date, output_directory)
