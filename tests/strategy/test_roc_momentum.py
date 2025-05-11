from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.strategy.momentum.roc_momentum import RocSignal, RoCSignalData, UniverseSpec


@pytest.fixture
def mock_price_data():
    # Create mock price data for testing with more realistic values
    # Extend the date range to ensure we have enough data for RoC calculation
    dates = pd.date_range(
        start="2022-12-01", end="2023-02-28", freq="B"
    )  # Extended date range
    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = []

    # Create a base price for each ticker
    base_prices = {"AAPL": 150.0, "MSFT": 250.0, "GOOGL": 100.0}

    # Create a trend for each ticker
    trends = {"AAPL": 0.005, "MSFT": 0.008, "GOOGL": -0.006}

    for i, date in enumerate(dates):
        for ticker in tickers:
            trend_factor = 1 + (trends[ticker] * i)
            random_factor = 1 + np.random.normal(0, 0.02)
            price = base_prices[ticker] * trend_factor * random_factor
            data.append({"date": date, "ticker": ticker, "value": price})

    return pd.DataFrame(data)


@pytest.fixture
def universe_spec():
    return UniverseSpec(
        universe="sp500",
        start_date="2022-12-01",
        end_date="2023-02-28",  # Updated to match mock data
    )


def test_roc_signal_initialization(universe_spec, mock_price_data):
    """Test that RocSignal initializes correctly with valid UniverseSpec"""
    with patch(
        "src.data_access.prices.PriceDataFetcher.get_price_data"
    ) as mock_get_price_data:
        mock_get_price_data.return_value = mock_price_data
        signal = RocSignal(universe_spec)
        assert signal.spec == universe_spec
        assert isinstance(signal.roc_data, RoCSignalData)


def test_calculate_signal_scores(universe_spec, mock_price_data):
    """Test the calculate_signal_scores function with mock data"""
    with patch(
        "src.data_access.prices.PriceDataFetcher.get_price_data"
    ) as mock_get_price_data:
        mock_get_price_data.return_value = mock_price_data
        signal = RocSignal(universe_spec)
        roc_diff = signal.calculate_signal_scores()

        # Verify the output is a DataFrame
        assert isinstance(roc_diff, pd.DataFrame)

        # Verify the output has the expected columns
        expected_columns = sorted(mock_price_data["ticker"].unique())
        assert all(col in roc_diff.columns for col in expected_columns)

        # Verify the index is datetime
        assert isinstance(roc_diff.index, pd.DatetimeIndex)

        # Verify the values are numeric
        assert roc_diff.select_dtypes(include=[np.number]).shape[1] == len(
            expected_columns
        )

        # Verify that after the initial NaN period, there are no NaN values
        # The first 3 weeks will have NaN values due to the 3-week RoC calculation
        non_nan_data = roc_diff.iloc[3:]  # Skip first 3 weeks
        assert not non_nan_data.isna().any().any()

        # Verify the shape of the output
        # We should have weekly data points
        assert len(roc_diff) > 0
        assert len(roc_diff.columns) == len(expected_columns)

        # Verify the values are reasonable (between -1 and 1 for RoC)
        assert (non_nan_data >= -1).all().all()  # RoC can't be less than -100%
        assert (non_nan_data <= 1).all().all()  # RoC can't be more than 100%
