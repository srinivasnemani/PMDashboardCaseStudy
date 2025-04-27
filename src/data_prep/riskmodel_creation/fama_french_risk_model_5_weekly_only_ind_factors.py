import os
import pickle
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Constants
CACHE_DIR = "risk_model_cache"
WEEKLY_MODELS_DIR = "weekly_risk_models_2024"
FF12_CACHE_FILE = os.path.join(CACHE_DIR, "ff12_industries.pkl")
SP500_CACHE_FILE = os.path.join(CACHE_DIR, "sp500_returns.pkl")
DEFAULT_HALFLIFE = 60
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(WEEKLY_MODELS_DIR, exist_ok=True)


class RiskModelUtils:
    @staticmethod
    def save_as_pickle(data, filepath):
        with open(filepath, "wb") as f:
            pickle.dump(data, f)
        print(f"Saved to {filepath}")

    @staticmethod
    def load_pickle(filepath):
        with open(filepath, "rb") as f:
            print(f"Loaded from {filepath}")
            return pickle.load(f)

    @staticmethod
    def get_or_cache_data(filepath, fetch_fn, *args, **kwargs):
        if os.path.exists(filepath):
            return RiskModelUtils.load_pickle(filepath)
        else:
            data = fetch_fn(*args, **kwargs)
            RiskModelUtils.save_as_pickle(data, filepath)
            return data

    @staticmethod
    def get_fridays_between_dates(start_date, end_date):
        # Expects start and  end date in the format "YYYY-MM-DD"
        return pd.date_range(start=start_date, end=end_date, freq="W-FRI").strftime('%Y-%m-%d').tolist()


class RiskModelDataFetcher:
    @staticmethod
    def fetch_ff12_industries(start_date, end_date):
        from pandas_datareader.famafrench import FamaFrenchReader
        print("Fetching Fama-French 12 industry portfolios...")
        ff = FamaFrenchReader('12_Industry_Portfolios_daily', start=start_date, end=end_date)
        df = ff.read()[0] / 100
        df.index = df.index.to_timestamp() if hasattr(df.index, 'to_timestamp') else df.index
        return df

    @staticmethod
    def fetch_sp500_returns(start_date, end_date):
        import yfinance as yf
        print("Fetching S&P 500 stock list...")
        sp500_table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        tickers = [t.replace('.', '-') for t in sp500_table['Symbol'].tolist()]

        all_data = pd.DataFrame()
        for i in range(0, len(tickers), 50):
            time.sleep(5)
            batch = tickers[i:i + 50]
            try:
                print(f"Fetching batch {i // 50 + 1}/{(len(tickers) // 50) + 1}")
                data = yf.download(batch, start=start_date, end=end_date)['Close']
                all_data = pd.concat([all_data, data], axis=1)
            except Exception as e:
                print(f"Error fetching batch: {e}")

        return all_data.pct_change()


class IndustryFactorRiskModel:
    def __init__(self, as_of_date=None):
        self.as_of_date = pd.Timestamp(as_of_date) if as_of_date else None
        self.stock_returns = None
        self.industry_factors = None
        self.industry_exposures = None
        self.specific_risk = None
        self.residuals = None
        self.factor_covariance = None

    def serialize_risk_model(self, filepath):
        data_dict = {
            'as_of_date': self.as_of_date,
            'stock_returns': self.stock_returns,
            'industry_factors': self.industry_factors,
            'industry_exposures': self.industry_exposures,
            'specific_risk': self.specific_risk,
            'residuals': self.residuals,
            'factor_covariance': self.factor_covariance,
        }
        RiskModelUtils.save_as_pickle(data_dict, filepath)

    @classmethod
    def load(cls, filepath):
        return RiskModelUtils.load_pickle(filepath)

    def load_data(self, stock_returns, industry_factors, window_days=252):
        start_date = self.as_of_date - pd.Timedelta(days=window_days + 30)
        self.stock_returns = stock_returns.loc[start_date:self.as_of_date]
        self.industry_factors = industry_factors.loc[start_date:self.as_of_date]
        common_dates = self.stock_returns.index.intersection(self.industry_factors.index)
        self.stock_returns = self.stock_returns.loc[common_dates]
        self.industry_factors = self.industry_factors.loc[common_dates]

    def estimate_exposures(self):
        industry_exposures = pd.DataFrame(index=self.stock_returns.columns, columns=self.industry_factors.columns)
        specific_risk = pd.Series(index=self.stock_returns.columns)
        residuals = pd.DataFrame(index=self.stock_returns.index, columns=self.stock_returns.columns)

        for stock in self.stock_returns.columns:
            if self.stock_returns[stock].isna().sum() > len(self.stock_returns) * 0.25:
                continue
            y = self.stock_returns[stock].dropna()
            X = self.industry_factors.loc[y.index].values
            X = np.column_stack([np.ones(X.shape[0]), X])
            model = LinearRegression(fit_intercept=False)
            model.fit(X, y.values.reshape(-1, 1))
            betas = model.coef_.flatten()[1:]
            industry_exposures.loc[stock] = betas
            pred = model.predict(X).flatten()
            residuals.loc[y.index, stock] = y.values - pred
            specific_risk[stock] = np.std(y.values - pred)

        self.industry_exposures = industry_exposures
        self.specific_risk = specific_risk
        last_date = residuals.index[-1]
        current_day_residuals = residuals.loc[[last_date]]
        self.residuals = current_day_residuals

    def calculate_factor_covariance(self, half_life=DEFAULT_HALFLIFE):
        n = len(self.industry_factors)
        weights = np.exp(np.arange(n) * (-np.log(2) / half_life))
        weights /= weights.sum()
        reversed_factors = self.industry_factors.iloc[::-1]
        means = np.average(reversed_factors, axis=0, weights=weights)
        demeaned = reversed_factors - means
        cov = np.cov(demeaned.T, aweights=weights)
        self.factor_covariance = pd.DataFrame(cov, index=self.industry_factors.columns,
                                              columns=self.industry_factors.columns)

    def build_complete_model(self, half_life=DEFAULT_HALFLIFE):
        self.estimate_exposures()
        self.calculate_factor_covariance(half_life=half_life)


def generate_weekly_risk_models(start_date='2024-01-01', end_date='2024-12-31'):
    sp500 = RiskModelUtils.get_or_cache_data(SP500_CACHE_FILE, RiskModelDataFetcher.fetch_sp500_returns, start_date,
                                             end_date)
    ff12 = RiskModelUtils.get_or_cache_data(FF12_CACHE_FILE, RiskModelDataFetcher.fetch_ff12_industries, start_date,
                                            end_date)

    fridays = RiskModelUtils.get_fridays_between_dates("2024-01-01", "2024-12-31")
    summary = []

    for date_str in fridays:
        date = pd.Timestamp(date_str)
        if date > pd.Timestamp.now():
            continue

        if date not in sp500.index:
            date = sp500.index[sp500.index <= date][-1]

        model_path = os.path.join(WEEKLY_MODELS_DIR, f"risk_model_{date.strftime('%Y-%m-%d')}.pkl")
        if os.path.exists(model_path):
            model = IndustryFactorRiskModel.load(model_path)
        else:
            model = IndustryFactorRiskModel(as_of_date=date)
            model.load_data(sp500, ff12)
            model.build_complete_model()
            model.serialize_risk_model(model_path)

        stat = {
            'Date': date,
            'Stocks_Count': model.stock_returns.shape[1],
            'Valid_Stocks': model.industry_exposures.dropna(how='all').shape[0],
            'Days_Used': len(model.stock_returns)
        }

        # Get industry correlations instead of market stats
        if model.factor_covariance is not None:
            corr = model.factor_covariance.corr().abs()
            mask = ~np.eye(corr.shape[0], dtype=bool)
            stat['Avg_Industry_Corr'] = corr.values[mask].mean()

            # Get the industry with highest volatility
            industry_vols = np.sqrt(np.diag(model.factor_covariance.values)) * np.sqrt(252)
            max_vol_idx = np.argmax(industry_vols)
            stat['Highest_Vol_Industry'] = model.factor_covariance.columns[max_vol_idx]
            stat['Highest_Industry_Vol'] = industry_vols[max_vol_idx]

        summary.append(stat)

    df_summary = pd.DataFrame(summary)
    df_summary.to_csv(os.path.join(WEEKLY_MODELS_DIR, "weekly_models_summary.csv"), index=False)

    plt.figure(figsize=(12, 8))
    plt.subplot(2, 1, 1)
    plt.plot(pd.to_datetime(df_summary['Date']), df_summary['Valid_Stocks'], marker='o')
    plt.title('Number of Valid Stocks with Industry Exposures')
    plt.grid(True)

    if 'Highest_Industry_Vol' in df_summary.columns:
        plt.subplot(2, 1, 2)
        plt.plot(pd.to_datetime(df_summary['Date']), df_summary['Highest_Industry_Vol'], marker='o', color='orange')
        plt.title('Annualized Highest Industry Volatility')
        plt.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(WEEKLY_MODELS_DIR, 'weekly_model_summary.png'))
    plt.show()

    return df_summary


if __name__ == '__main__':
    generate_weekly_risk_models()