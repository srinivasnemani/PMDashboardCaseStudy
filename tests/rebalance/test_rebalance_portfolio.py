import pandas as pd
import numpy as np
from datetime import date, datetime
from src.rebalance.rebalance_portfolio import (
    RebalanceData,
    create_rebalance_data,
    RebalanceUtil,
    RebalancePortfolio
)


def test_create_rebalance_data():
    # Test data creation
    strategy_name = "test_strategy"
    rebalance_date = date(2023, 1, 1)
    alpha_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'weight': [0.4, 0.3, 0.3],
        'trade_direction': ['Long', 'Long', 'Short']
    })
    prices_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'value': [150.0, 250.0, 100.0]
    })
    target_value = 10000.0

    rebalance_data = create_rebalance_data(
        strategy_name=strategy_name,
        rebalance_date=rebalance_date,
        alpha_df=alpha_df,
        prices_df=prices_df,
        rebalance_target_value=target_value
    )

    assert isinstance(rebalance_data, RebalanceData)
    assert rebalance_data.strategy_name == strategy_name
    assert rebalance_data.rebalance_date == rebalance_date
    assert rebalance_data.alpha_df.equals(alpha_df)
    assert rebalance_data.prices_df.equals(prices_df)
    assert rebalance_data.rebalance_target_value == target_value


def test_rebalance_portfolio_basic():
    # Test basic portfolio rebalancing
    strategy_name = "test_strategy"
    rebalance_date = date(2023, 1, 1)
    alpha_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'weight': [0.4, 0.3, 0.3],
        'trade_direction': ['Long', 'Long', 'Short']
    })
    prices_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'value': [150.0, 250.0, 100.0]
    })
    target_value = 10000.0

    rebalance_data = create_rebalance_data(
        strategy_name=strategy_name,
        rebalance_date=rebalance_date,
        alpha_df=alpha_df,
        prices_df=prices_df,
        rebalance_target_value=target_value
    )

    rebalancer = RebalancePortfolio(rebalance_data)
    result = rebalancer.rebalance_portfolio(rebalance_data)

    # Check result structure
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert all(col in result.columns for col in [
        'trade_open_date', 'ticker', 'shares', 'trade_open_price',
        'direction', 'trade_close_date', 'trade_close_price', 'strategy_name'
    ])

    # Check values
    assert result['strategy_name'].iloc[0] == strategy_name
    assert result['trade_open_date'].iloc[0] == rebalance_date
    assert all(result['direction'].isin(['Long', 'Short']))
    assert all(result['shares'] != 0)


def test_rebalance_portfolio_zero_prices():
    # Test rebalancing with zero prices
    strategy_name = "test_strategy"
    rebalance_date = date(2023, 1, 1)
    alpha_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'weight': [0.4, 0.3, 0.3],
        'trade_direction': ['Long', 'Long', 'Short']
    })
    prices_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'value': [0.0, 0.0, 0.0]
    })
    target_value = 10000.0

    rebalance_data = create_rebalance_data(
        strategy_name=strategy_name,
        rebalance_date=rebalance_date,
        alpha_df=alpha_df,
        prices_df=prices_df,
        rebalance_target_value=target_value
    )

    rebalancer = RebalancePortfolio(rebalance_data)
    result = rebalancer.rebalance_portfolio(rebalance_data)

    # Should return empty DataFrame when all prices are zero
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_rebalance_portfolio_single_direction():
    # Test rebalancing with only long positions
    strategy_name = "test_strategy"
    rebalance_date = date(2023, 1, 1)
    alpha_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'weight': [0.4, 0.3, 0.3],
        'trade_direction': ['Long', 'Long', 'Long']
    })
    prices_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'value': [150.0, 250.0, 100.0]
    })
    target_value = 10000.0

    rebalance_data = create_rebalance_data(
        strategy_name=strategy_name,
        rebalance_date=rebalance_date,
        alpha_df=alpha_df,
        prices_df=prices_df,
        rebalance_target_value=target_value
    )

    rebalancer = RebalancePortfolio(rebalance_data)
    result = rebalancer.rebalance_portfolio(rebalance_data)

    # Check that all positions are long
    assert all(result['direction'] == 'Long')
    assert all(result['shares'] > 0)


def test_rebalance_portfolio_short_positions():
    # Test rebalancing with only short positions
    strategy_name = "test_strategy"
    rebalance_date = date(2023, 1, 1)
    alpha_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'weight': [0.4, 0.3, 0.3],
        'trade_direction': ['Short', 'Short', 'Short']
    })
    prices_df = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'value': [150.0, 250.0, 100.0]
    })
    target_value = 10000.0

    rebalance_data = create_rebalance_data(
        strategy_name=strategy_name,
        rebalance_date=rebalance_date,
        alpha_df=alpha_df,
        prices_df=prices_df,
        rebalance_target_value=target_value
    )

    rebalancer = RebalancePortfolio(rebalance_data)
    result = rebalancer.rebalance_portfolio(rebalance_data)

    # Check that all positions are short
    assert all(result['direction'] == 'Short')
    assert all(result['shares'] < 0)


def test_get_new_portfolio_notional_initial():
    # Test initial portfolio notional calculation
    aum_leverage_df = pd.DataFrame({
        'date': ['2023-01-01'],
        'aum': [1000000.0],
        'target_leverage': [2.0],
        'in_out_flows': [0.0],
        'leverage_change': [0.0]
    })
    
    current_pf_value = 0.0
    rebalance_date = '2023-01-01'
    
    result = RebalanceUtil.get_new_portfolio_notional(
        aum_leverage_df,
        rebalance_date,
        current_pf_value,
        is_initial_rebalance=True
    )
    
    assert result == 2000000.0  # 1,000,000 * 2.0


def test_get_new_portfolio_notional_subsequent():
    # Test subsequent portfolio notional calculation
    aum_leverage_df = pd.DataFrame({
        'date': ['2023-01-01'],
        'aum': [1000000.0],
        'target_leverage': [2.0],
        'in_out_flows': [100000.0],  # New capital inflow
        'leverage_change': [0.5]  # Leverage increase
    })
    
    current_pf_value = 1500000.0
    rebalance_date = '2023-01-01'
    
    result = RebalanceUtil.get_new_portfolio_notional(
        aum_leverage_df,
        rebalance_date,
        current_pf_value,
        is_initial_rebalance=False
    )
    
    # Expected calculation:
    # current_portfolio_value_with_out_leverage = 1500000 / (2.0 - 0.5) = 1000000
    # leverage_increase = 2.0 * 1000000 = 2000000
    # new_capital_inflows = 2.0 * 100000 = 200000
    # total = 2200000
    assert abs(result - 2200000.0) < 1e-10 