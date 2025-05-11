from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.data_access.schemas import UniverseSpec
from src.strategy.min_vol.min_vol import MinVolSignal, MinVolSignalData


@pytest.fixture
def mock_price_data():
    # Create mock price data for testing with more realistic values
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
def mock_benchmark_data():
    # Create mock benchmark data (SPY prices)
    dates = pd.date_range(start="2022-12-01", end="2023-02-28", freq="B")
    data = []

    # Create a base price for SPY
    base_price = 400.0
    trend = 0.003

    for i, date in enumerate(dates):
        trend_factor = 1 + (trend * i)
        random_factor = 1 + np.random.normal(0, 0.01)
        price = base_price * trend_factor * random_factor
        data.append({"date": date, "ticker": "SPY", "value": price})

    return pd.DataFrame(data)


@pytest.fixture
def universe_spec():
    return UniverseSpec(
        universe="sp500",
        start_date="2022-12-01",
        end_date="2023-02-28",  # Updated to match mock data
    )


def test_min_vol_signal_initialization(
    universe_spec, mock_price_data, mock_benchmark_data
):
    """Test that MinVolSignal initializes correctly with valid UniverseSpec"""
    # Create a mock MinVolSignalData instance
    mock_min_vol_data = MagicMock(spec=MinVolSignalData)
    mock_min_vol_data.price_data = mock_price_data
    mock_min_vol_data.benchmark_data = mock_benchmark_data

    # Patch both the PriceDataFetcher and MinVolSignalData
    with patch(
        "src.data_access.prices.PriceDataFetcher.get_price_data"
    ) as mock_get_price_data, patch(
        "src.strategy.min_vol.min_vol.MinVolSignalData", return_value=mock_min_vol_data
    ):
        mock_get_price_data.return_value = mock_price_data
        signal = MinVolSignal(universe_spec)
        assert signal.spec == universe_spec
        assert isinstance(signal.min_vol_data, MagicMock)
        assert signal.min_vol_data.price_data.equals(mock_price_data)
        assert signal.min_vol_data.benchmark_data.equals(mock_benchmark_data)


def test_calculate_signal_scores(universe_spec, mock_price_data, mock_benchmark_data):
    """Test the calculate_signal_scores function with mock data"""
    # Create a mock MinVolSignalData instance
    mock_min_vol_data = MagicMock(spec=MinVolSignalData)
    mock_min_vol_data.price_data = mock_price_data
    mock_min_vol_data.benchmark_data = mock_benchmark_data

    # Patch both the PriceDataFetcher and MinVolSignalData
    with patch(
        "src.data_access.prices.PriceDataFetcher.get_price_data"
    ) as mock_get_price_data, patch(
        "src.strategy.min_vol.min_vol.MinVolSignalData", return_value=mock_min_vol_data
    ):
        mock_get_price_data.return_value = mock_price_data
        signal = MinVolSignal(universe_spec)
        min_vol_scores = signal.calculate_signal_scores()

        # Verify the output is a DataFrame
        assert isinstance(min_vol_scores, pd.DataFrame)

        # Verify the output has the expected columns
        expected_columns = sorted(mock_price_data["ticker"].unique())
        assert all(col in min_vol_scores.columns for col in expected_columns)

        # Verify the index is datetime
        assert isinstance(min_vol_scores.index, pd.DatetimeIndex)

        # Verify the values are numeric
        assert min_vol_scores.select_dtypes(include=[np.number]).shape[1] == len(
            expected_columns
        )

        # Verify no NaN values in the output
        assert not min_vol_scores.isna().any().any()
