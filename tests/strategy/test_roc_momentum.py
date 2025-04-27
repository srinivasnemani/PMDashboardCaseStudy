import numpy as np
import pandas as pd
import pytest

from src.strategy.momentum.roc_momentum import (RocSignal, RoCSignalData,
                                                UniverseSpec)


@pytest.fixture
def mock_price_data():
    # Create mock price data for testing with more realistic values
    # Extend the date range to ensure we have enough data for RoC calculation
    dates = pd.date_range(start='2022-12-01', end='2023-01-31', freq='B')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'WMT']
    data = []

    # Create a base price for each ticker
    base_prices = {
        'AAPL': 150.0,
        'MSFT': 250.0,
        'GOOGL': 100.0,
        'AMZN': 90.0,
        'META': 200.0,
        'TSLA': 180.0,
        'NVDA': 300.0,
        'JPM': 140.0,
        'V': 220.0,
        'WMT': 150.0
    }

    # Create a trend for each ticker with more pronounced movements
    trends = {
        'AAPL': 0.005,  # More pronounced upward trend
        'MSFT': 0.008,
        'GOOGL': -0.006,  # More pronounced downward trend
        'AMZN': 0.009,
        'META': -0.007,
        'TSLA': 0.012,
        'NVDA': 0.008,
        'JPM': -0.005,
        'V': 0.006,
        'WMT': 0.007
    }

    for i, date in enumerate(dates):
        for ticker in tickers:
            # Add trend and random variation to make the data more realistic
            trend_factor = 1 + (trends[ticker] * i)
            random_factor = 1 + np.random.normal(0, 0.02)  # Increased random variation
            price = base_prices[ticker] * trend_factor * random_factor
            data.append({
                'date': date,
                'ticker': ticker,
                'value': price
            })

    return pd.DataFrame(data)


@pytest.fixture
def universe_spec():
    return UniverseSpec(
        universe='sp500',
        start_date='2022-12-01',  # Updated to match mock data
        end_date='2023-01-31'
    )


def test_roc_signal_initialization(universe_spec):
    """Test that RocSignal initializes correctly with valid UniverseSpec"""
    signal = RocSignal(universe_spec)
    assert signal.spec == universe_spec
    assert isinstance(signal.roc_data, RoCSignalData)
