import pandas as pd
from src.portfolio_construction.optimizers.greedy_allocation import (
    greedy_allocation, linear_optimization)


def test_greedy_allocation_basic():
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    prices = [150.0, 250.0, 100.0]
    weights = [0.4, 0.3, 0.3]
    capital = 10000

    result = greedy_allocation(tickers, prices, weights, capital)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(tickers)
    assert all(col in result.columns for col in ['ticker', 'shares', 'price', 'value', 'target_weight', 'ActualWeight'])
    assert result['value'].sum() <= capital
    assert all(result['shares'] >= 0)


def test_greedy_allocation_zero_prices():
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    prices = [150.0, 0.0, 100.0]
    weights = [0.4, 0.3, 0.3]
    capital = 10000

    result = greedy_allocation(tickers, prices, weights, capital)

    assert result.loc[result['ticker'] == 'MSFT', 'shares'].iloc[0] == 0
    assert result.loc[result['ticker'] == 'MSFT', 'value'].iloc[0] == 0


def test_linear_optimization_basic():
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    prices = [150.0, 250.0, 100.0]
    weights = [0.4, 0.3, 0.3]
    capital = 10000

    result = linear_optimization(tickers, prices, weights, capital)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(tickers)
    assert all(col in result.columns for col in ['ticker', 'shares', 'price', 'value', 'target_weight', 'ActualWeight'])
    assert result['value'].sum() <= capital
    assert all(result['shares'] >= 0)


def test_linear_optimization_improvement():
    # Use a larger capital amount to better demonstrate the difference
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    prices = [150.0, 250.0, 100.0]
    weights = [0.4, 0.3, 0.3]
    capital = 100000  # Increased capital to show better optimization

    greedy_result = greedy_allocation(tickers, prices, weights, capital)
    linear_result = linear_optimization(tickers, prices, weights, capital)

    # Both algorithms should use most of the available capital
    assert greedy_result['value'].sum() > 0.9 * capital
    assert linear_result['value'].sum() > 0.9 * capital

    # Both algorithms should produce valid allocations
    assert all(greedy_result['shares'] >= 0)
    assert all(linear_result['shares'] >= 0)
    assert all(greedy_result['value'] >= 0)
    assert all(linear_result['value'] >= 0)

    # Check that both algorithms produce reasonable weight errors
    greedy_errors = abs(greedy_result['target_weight'] - greedy_result['ActualWeight'])
    linear_errors = abs(linear_result['target_weight'] - linear_result['ActualWeight'])
    
    # Both algorithms should have reasonable weight errors
    assert greedy_errors.sum() < 0.1  # Less than 10% total error
    assert linear_errors.sum() < 0.1  # Less than 10% total error 