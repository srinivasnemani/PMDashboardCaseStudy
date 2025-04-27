import pandas as pd
import numpy as np
from src.portfolio_construction.optimizers.create_portfolio_weights import construct_portfolio_weights


def test_construct_portfolio_weights_basic():
    # Create sample data
    data = pd.DataFrame({
        'AAPL': [1.0, 2.0, 3.0],
        'MSFT': [2.0, 3.0, 4.0],
        'GOOGL': [3.0, 4.0, 5.0]
    }, index=pd.date_range('2023-01-01', periods=3))
    
    strategy_name = "test_strategy"
    result = construct_portfolio_weights(data, strategy_name)
    
    # Check that result is a DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Check required columns
    assert all(col in result.columns for col in [
        'date', 'trade_direction', 'ticker', 'alpha_score', 'weight', 'strategy_name'
    ])
    
    # Check strategy name
    assert all(result['strategy_name'] == strategy_name)
    
    # Check that weights sum to 1 for each date and direction
    for date in data.index:
        for direction in ['Long', 'Short']:
            mask = (result['date'] == date) & (result['trade_direction'] == direction)
            if any(mask):
                assert abs(result.loc[mask, 'weight'].sum() - 1.0) < 1e-10


def test_construct_portfolio_weights_insufficient_data():
    # Create sample data with insufficient rows
    data = pd.DataFrame({
        'AAPL': [1.0],
        'MSFT': [2.0],
        'GOOGL': [3.0]
    }, index=pd.date_range('2023-01-01', periods=1))
    
    strategy_name = "test_strategy"
    result = construct_portfolio_weights(data, strategy_name, top_n=2)
    
    # Should return valid DataFrame with balanced long/short positions
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    
    # Check that we have both long and short positions
    assert set(result['trade_direction']) == {'Long', 'Short'}
    
    # Check that weights sum to 1 for each direction
    for direction in ['Long', 'Short']:
        mask = result['trade_direction'] == direction
        assert abs(result.loc[mask, 'weight'].sum() - 1.0) < 1e-10


def test_construct_portfolio_weights_zero_data():
    # Create sample data with all zeros
    data = pd.DataFrame({
        'AAPL': [0.0, 0.0, 0.0],
        'MSFT': [0.0, 0.0, 0.0],
        'GOOGL': [0.0, 0.0, 0.0]
    }, index=pd.date_range('2023-01-01', periods=3))
    
    strategy_name = "test_strategy"
    result = construct_portfolio_weights(data, strategy_name)
    
    # Should return empty DataFrame when all scores are zero
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_construct_portfolio_weights_single_asset():
    # Create sample data with single asset
    data = pd.DataFrame({
        'AAPL': [1.0, 2.0, 3.0]
    }, index=pd.date_range('2023-01-01', periods=3))
    
    strategy_name = "test_strategy"
    result = construct_portfolio_weights(data, strategy_name, top_n=1)
    
    # Should return DataFrame with single asset long position
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert all(result['trade_direction'] == 'Long')
    assert all(result['ticker'] == 'AAPL')
    assert all(result['weight'] == 1.0) 