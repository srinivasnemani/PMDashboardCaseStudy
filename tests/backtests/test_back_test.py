from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from src.back_test import BackTestUtil, create_backtest_data


@pytest.fixture
def test_data():
    """Fixture providing common test data"""
    return {
        "strategy_name": "TestStrategy",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "price_history": pd.DataFrame(
            {
                "date": [date(2024, 1, 1), date(2024, 1, 2)],
                "ticker": ["AAPL", "MSFT"],
                "value": [100.0, 200.0],
            }
        ),
        "alpha_scores": pd.DataFrame(
            {
                "date": [date(2024, 1, 1), date(2024, 1, 2)],
                "ticker": ["AAPL", "MSFT"],
                "score": [0.5, 0.7],
                "trade_direction": ["LONG", "SHORT"],
                "weight": [0.6, 0.4],
            }
        ),
        "aum_leverage": pd.DataFrame(
            {
                "date": [date(2024, 1, 1), date(2024, 1, 2)],
                "aum": [1000000.0, 1100000.0],
                "leverage": [1.0, 1.1],
            }
        ),
    }


def test_create_backtest_data(test_data):
    """Test creation of BackTestData object"""
    with patch(
        "src.back_test.back_test.PriceDataFetcher.get_price_data"
    ) as mock_price, patch(
        "src.back_test.back_test.RebalanceUtil.get_alpha_scores"
    ) as mock_alpha, patch(
        "src.back_test.back_test.RebalanceUtil.get_aum_leverage_data"
    ) as mock_aum:

        mock_price.return_value = test_data["price_history"]
        mock_alpha.return_value = test_data["alpha_scores"]
        mock_aum.return_value = test_data["aum_leverage"]

        backtest_data = create_backtest_data(
            test_data["strategy_name"], test_data["start_date"], test_data["end_date"]
        )

        assert backtest_data.strategy_name == test_data["strategy_name"]
        assert backtest_data.start_date == test_data["start_date"]
        assert backtest_data.end_date == test_data["end_date"]
        assert backtest_data.price_history_df is not None
        assert backtest_data.alpha_scores_df is not None
        assert backtest_data.aum_leverage_df is not None


def test_get_previous_rebalance_data(test_data):
    """Test getting previous rebalance data"""
    mock_db_result = pd.DataFrame(
        {
            "trade_open_date": [date(2024, 1, 1)],
            "strategy_name": ["TestStrategy"],
            "ticker": ["AAPL"],
            "shares": [100],
            "trade_open_price": [150.0],
        }
    )

    with patch(
        "src.back_test.back_test.DataAccessUtil.fetch_data_from_db"
    ) as mock_fetch:
        mock_fetch.return_value = mock_db_result

        result = BackTestUtil.get_previous_rebalance_data(
            test_data["strategy_name"], date(2024, 1, 2)
        )

        assert result is not None
        assert len(result) == 1
        assert result["ticker"].iloc[0] == "AAPL"


def test_fill_trade_closing_prices(test_data):
    """Test filling trade closing prices"""
    prev_trades = pd.DataFrame(
        {
            "ticker": ["AAPL", "MSFT"],
            "shares": [100, 200],
            "trade_open_price": [150.0, 250.0],
        }
    )

    closing_prices = pd.DataFrame({"ticker": ["AAPL", "MSFT"], "value": [160.0, 260.0]})

    result = BackTestUtil.fill_trade_closing_prices(
        prev_trades, closing_prices, date(2024, 1, 2)
    )

    assert "trade_close_price" in result.columns
    assert "trade_close_date" in result.columns
    assert result["trade_close_price"].iloc[0] == 160.0
    assert result["trade_close_date"].iloc[0].date() == date(2024, 1, 2)
