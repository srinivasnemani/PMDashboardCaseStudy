import numpy as np
import pandas as pd

from src.portfolio_construction.optimizers.cvxpy_optimizer import cvx_optimizer


def test_cvx_optimizer_basic():
    # Create sample data
    tickers = ["AAPL", "MSFT", "GOOGL"]
    prices = [150.0, 250.0, 100.0]
    weights = [0.4, 0.3, 0.3]
    capital = 10000

    result = cvx_optimizer(tickers, prices, weights, capital)

    # Check that result is a DataFrame
    assert isinstance(result, pd.DataFrame)

    # Check that all required columns are present
    assert all(
        col in result.columns
        for col in [
            "ticker",
            "shares",
            "price",
            "value",
            "target_weight",
            "actual_weight",
        ]
    )

    # Check that shares are non-negative integers
    assert all(result["shares"] >= 0)
    assert all(isinstance(x, (int, np.integer)) for x in result["shares"])

    # Check that total value doesn't exceed capital
    assert result["value"].sum() <= capital

    # Check that weights sum to approximately 1
    assert abs(result["actual_weight"].sum() - 1.0) < 1e-10


def test_cvx_optimizer_zero_prices():
    # Test with zero prices
    tickers = ["AAPL", "MSFT", "GOOGL"]
    prices = [150.0, 0.0, 100.0]
    weights = [0.4, 0.3, 0.3]
    capital = 10000

    result = cvx_optimizer(tickers, prices, weights, capital)

    # Check that zero price results in zero shares
    assert result.loc[result["ticker"] == "MSFT", "shares"].iloc[0] == 0
    assert result.loc[result["ticker"] == "MSFT", "value"].iloc[0] == 0


def test_cvx_optimizer_single_asset():
    # Test with single asset
    tickers = ["AAPL"]
    prices = [150.0]
    weights = [1.0]
    capital = 10000

    result = cvx_optimizer(tickers, prices, weights, capital)

    # Check single asset allocation
    assert len(result) == 1
    assert result["ticker"].iloc[0] == "AAPL"
    assert result["shares"].iloc[0] > 0
    assert result["actual_weight"].iloc[0] == 1.0
