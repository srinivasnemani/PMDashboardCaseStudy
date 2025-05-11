import numpy as np
import pandas as pd
import pytest

from data_access.schemas import UniverseSpec
from src.strategy.min_vol.min_vol import (MinVolSignal, MinVolSignalData,
                                          PriceDataFetcher)


@pytest.fixture
def mock_price_data():
    dates = pd.date_range(start="2023-01-01", periods=20, freq="B")
    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = {
        "date": np.repeat(dates, len(tickers)),
        "ticker": np.tile(tickers, len(dates)),
        "value": np.random.normal(100, 10, len(dates) * len(tickers)),
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_benchmark_data():
    dates = pd.date_range(start="2023-01-01", periods=20, freq="B")
    tickers = ["SPY"]
    data = {
        "date": np.repeat(dates, len(tickers)),
        "ticker": np.tile(tickers, len(dates)),
        "value": np.random.normal(100, 5, len(dates) * len(tickers)),
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_universe_spec():
    return UniverseSpec(
        universe="sp500", start_date="2023-01-01", end_date="2023-01-31"
    )


def test_min_vol_signal_data_initialization(
    mock_universe_spec, mock_price_data, mock_benchmark_data, monkeypatch
):
    # Mock the PriceDataFetcher methods
    monkeypatch.setattr(
        PriceDataFetcher, "get_price_data", lambda *args, **kwargs: mock_price_data
    )
    monkeypatch.setattr(
        PriceDataFetcher,
        "get_benchmark_data",
        lambda *args, **kwargs: mock_benchmark_data,
    )

    # Initialize MinVolSignalData
    signal_data = MinVolSignalData(mock_universe_spec)

    # Verify the data was loaded correctly
    assert isinstance(signal_data.price_data, pd.DataFrame)
    assert isinstance(signal_data.benchmark_data, pd.DataFrame)
    assert not signal_data.price_data.empty
    assert not signal_data.benchmark_data.empty


def test_min_vol_signal_initialization(mock_universe_spec):
    signal = MinVolSignal(mock_universe_spec)
    assert signal.spec == mock_universe_spec
    assert isinstance(signal.min_vol_data, MinVolSignalData)


def test_calculate_signal_scores_shape_and_type(
    mock_universe_spec, mock_price_data, mock_benchmark_data, monkeypatch
):
    # Mock the PriceDataFetcher methods
    monkeypatch.setattr(
        PriceDataFetcher, "get_price_data", lambda *args, **kwargs: mock_price_data
    )
    monkeypatch.setattr(
        PriceDataFetcher,
        "get_benchmark_data",
        lambda *args, **kwargs: mock_benchmark_data,
    )

    signal = MinVolSignal(mock_universe_spec)
    signal_scores = signal.calculate_signal_scores(signal.min_vol_data)

    # Verify the output shape and type
    assert isinstance(signal_scores, pd.DataFrame)
    assert not signal_scores.empty
    assert "date" in signal_scores.index.name
    assert all(ticker in signal_scores.columns for ticker in ["AAPL", "MSFT", "GOOGL"])


def test_calculate_signal_scores_values(
    mock_universe_spec, mock_price_data, mock_benchmark_data, monkeypatch
):
    # Mock the PriceDataFetcher methods
    monkeypatch.setattr(
        PriceDataFetcher, "get_price_data", lambda *args, **kwargs: mock_price_data
    )
    monkeypatch.setattr(
        PriceDataFetcher,
        "get_benchmark_data",
        lambda *args, **kwargs: mock_benchmark_data,
    )

    signal = MinVolSignal(mock_universe_spec)
    signal_scores = signal.calculate_signal_scores(signal.min_vol_data)

    # Verify the signal values make sense
    # Signal should be negative (lower volatility is better)
    assert (signal_scores <= 0).all().all()

    # Check for NaN values in the middle of the series (should be cleaned)
    assert not signal_scores.iloc[5:-5].isna().any().any()

    # Verify the rolling window calculation
    # The signal should have 10 rows because:
    # - We have 20 business days
    # - First 9 days are used for the initial rolling window
    # - Remaining 11 days have signal values
    # - The last day might be dropped due to forward-fill
    assert len(signal_scores) == 10
