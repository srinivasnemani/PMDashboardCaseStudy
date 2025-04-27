import numpy as np
import pandas as pd
import yfinance as yf


# Step 1: Get S&P 500 tickers using pandas (Wikipedia)
def get_sp500_tickers():
    try:
        # Read Wikipedia table using pandas
        sp500_info = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        sp500_info = sp500_info[['Symbol']]
        sp500_info['Symbol'] = sp500_info['Symbol'].str.replace('.', '-', regex=False)
        return sp500_info['Symbol'].tolist()
    except Exception as e:
        print(f"Error getting S&P 500 information: {e}")
        return []

# Step 2: Fetch data from Yahoo Finance
def fetch_fundamental_data(tickers):
    data = []
    for ticker in tickers[1:25]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(start="2024-01-01", end="2024-12-31")

            if hist.empty:
                continue

            latest_close = hist["Close"].iloc[-1]
            market_cap = info.get("marketCap", np.nan)

            data.append({
                "Ticker": ticker,
                "PriceToBook": info.get("priceToBook", np.nan),
                "LogMarketCap": np.log(market_cap) if market_cap else np.nan,
                "ReturnOnEquity": info.get("returnOnEquity", np.nan),
                "Beta": info.get("beta", np.nan),
                "DebtToEquity": info.get("debtToEquity", np.nan),
                "EarningsGrowth": info.get("earningsGrowth", np.nan),
                "TrailingEPS": info.get("trailingEps", np.nan),
                "AnalystRecommendationMean": info.get("recommendationMean", np.nan),
                "ShortPercentOfFloat": info.get("shortPercentOfFloat", np.nan)
            })
        except Exception as e:
            print(f"Failed for {ticker}: {e}")
    return pd.DataFrame(data)

# Step 3: Main execution
if __name__ == "__main__":
    tickers = get_sp500_tickers()
    df_factors = fetch_fundamental_data(tickers)
    df_factors.to_csv("sp500_fundamentals_2024.csv", index=False)
    print("Data saved to sp500_fundamentals_2024.csv")
