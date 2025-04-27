import pandas as pd
from sqlalchemy import text

from src.analytics.back_test_summary import (BackTestSummaryAnalytics,
                                             BackTestSummaryAnalyticsData)
from src.analytics.trade_summary import get_pnl_time_series_from_trade_data
from src.data_access.crud_util import DataAccessUtil
from src.data_access.prices import PriceDataFetcher
from src.data_access.schemas import UniverseSpec

DEFAULT_RISK_FREE_RATE = 0.02


def get_bm_data():
    univ_spec = UniverseSpec("SP500", "2024-01-01", "2024-12-31")
    bm_data = PriceDataFetcher.get_benchmark_data(univ_spec)
    bm_data = bm_data.sort_values('date')
    bm_data['benchmark_returns'] = bm_data['value'].pct_change()
    return bm_data


def get_backtest_data(strategy_name, trade_direction, start_date, end_date):
    sql_query = f""" SELECT * FROM trade_booking tb where 
                    tb.strategy_name  = "{strategy_name}"
                    and tb.trade_open_date >= date('{start_date}')
                    and tb.trade_open_date <= date('{end_date}') """

    query_string = text(sql_query)
    back_test_data = DataAccessUtil.fetch_data_from_db(query_string)

    if trade_direction.capitalize() == "Long":
        back_test_data = back_test_data[back_test_data['direction'] == "Long"]
    elif trade_direction.capitalize() == "Short":
        back_test_data = back_test_data[back_test_data['direction'] == "Short"]

    back_test_returns = get_pnl_time_series_from_trade_data(back_test_data)
    back_test_returns['trade_open_date'] = pd.to_datetime(back_test_returns['trade_open_date'])
    back_test_returns = back_test_returns.rename(columns={'trade_pnl_pct': 'portfolio_returns'})
    back_test_returns = back_test_returns.rename(columns={'trade_open_date': 'date'})

    return back_test_returns


def align_pf_bm_data(trade_pnl_df, bm_data):
    combined_df = pd.merge(trade_pnl_df, bm_data, on='date', how='left')
    selected_columns = ['date', 'portfolio_returns', 'benchmark_returns']
    combined_df = combined_df[selected_columns]
    return combined_df


def append_risk_free_rate(df, risk_free_rate=DEFAULT_RISK_FREE_RATE):
    # Sort dates to ensure proper calculation
    df = df.sort_values('date')

    # Calculate most common difference between dates
    diff = df['date'].diff().mode()[0]

    if diff.days == 1:
        frequency = 'D'
        days_per_period = 1
    elif diff.days == 7:
        frequency = 'W'
        days_per_period = 7
    elif 28 <= diff.days <= 31:
        frequency = 'M'
        days_per_period = 30
    else:
        frequency = f'{diff.days}D'
        days_per_period = diff.days

    # Convert annual risk-free rate to the appropriate frequency
    # Using (1+r)^(days/365) - 1 formula for compounding
    risk_free_period_rate = (1 + risk_free_rate) ** (days_per_period / 365) - 1

    # Create a new column with the risk-free rate adjusted for frequency
    df['risk_free_rate'] = risk_free_period_rate

    return df


def create_back_test_summary(strategy_name, start_date=None, end_date=None, trade_direction="all"):
    benchmark_data = get_bm_data()
    portfolio_data = get_backtest_data(strategy_name, trade_direction, start_date, end_date)


    combined = align_pf_bm_data(portfolio_data, benchmark_data)
    combined = combined.sort_values(['date'])
    bm_pf_rf_df = append_risk_free_rate(combined)
    back_test_data = BackTestSummaryAnalyticsData(bm_pf_rf_df)

    # Create backtesting object
    backtest_analytics = BackTestSummaryAnalytics(backtest_data=back_test_data)
    backtest_summary = backtest_analytics.summary()
    return backtest_summary


def format_dataframe(df, format_dict):
    formatter = {}

    for col in df.columns:
        for pattern, fmt in format_dict.items():
            if pattern in col:
                formatter[col] = fmt
                break

    return df.style.format(formatter)


if __name__ == "__main__":
    v1 = create_back_test_summary("MinVol", "2024-01-01", "2024-12-31", "Long")

    format_map = {
        'Absolute Return': '{:.2%}',
        'Annualized Return': '{:.2%}',
        'Cumulative Return': '{:.2%}',
        'Sharpe Ratio': '{:.2f}',
        'Sortino Ratio': '{:.2f}',
        'Information Ratio': '{:.2f}',
        'Volatility': '{:.2%}',
        'Beta': '{:.2f}',
        'Alpha': '{:.2%}',
        'Maximum Drawdown': '{:.2%}',
        'Calmar Ratio': '{:.2f}'
    }
    v3 = v1.style.format(format_map)
    print(v3)
