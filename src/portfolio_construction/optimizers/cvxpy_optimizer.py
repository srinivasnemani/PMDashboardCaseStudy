import cvxpy as cp
import numpy as np
import pandas as pd


def cvx_optimizer(tickers, prices, weights_target, capital=1_000_000):
    """
    Optimize portfolio allocation based on target weights.

    Parameters:
    tickers: List of ticker symbols
    prices: Array of prices for each ticker
    weights_target: Target portfolio weights
    capital: Total capital to invest

    Returns:
    DataFrame with optimization results
    """
    # Convert inputs to numpy arrays
    prices = np.array(prices, dtype=float)
    weights_target = np.array(weights_target, dtype=float)
    
    # Handle zero prices
    if np.any(prices == 0):
        zero_price_indices = np.where(prices == 0)[0]
        print(f"Warning: Zero prices found for tickers: {[tickers[i] for i in zero_price_indices]}")
        
        # Create result DataFrame with zero shares for zero-price assets
        result_df = pd.DataFrame({
            "ticker": tickers,
            "shares": np.zeros(len(tickers), dtype=int),
            "price": prices,
            "value": np.zeros(len(tickers)),
            "target_weight": weights_target,
            "actual_weight": np.zeros(len(tickers))
        })
        
        # Only optimize for non-zero prices
        valid_indices = np.where(prices > 0)[0]
        if len(valid_indices) == 0:
            return result_df
            
        # Adjust weights for remaining assets
        remaining_weight = weights_target[zero_price_indices].sum()
        if remaining_weight > 0:
            weights_target[valid_indices] *= (1 + remaining_weight) / weights_target[valid_indices].sum()
        
        # Optimize for valid prices
        valid_tickers = [tickers[i] for i in valid_indices]
        valid_prices = prices[valid_indices]
        valid_weights = weights_target[valid_indices]
        
        # Normalize valid weights to sum to 1
        valid_weights = valid_weights / valid_weights.sum()
        
        try:
            valid_result = _optimize_portfolio(valid_tickers, valid_prices, valid_weights, capital)
            
            # Update result DataFrame with optimized values
            for col in valid_result.columns:
                result_df.loc[valid_indices, col] = valid_result[col]
                
            return result_df
            
        except Exception as e:
            print(f"Error in optimization: {str(e)}")
            return result_df
    
    # If no zero prices, optimize normally
    try:
        return _optimize_portfolio(tickers, prices, weights_target, capital)
    except Exception as e:
        print(f"Error in optimization: {str(e)}")
        return pd.DataFrame(columns=["ticker", "shares", "price", "value", "target_weight", "actual_weight"])


def _optimize_portfolio(tickers, prices, weights_target, capital):
    """Internal function to perform the optimization."""
    n = len(tickers)
    x = cp.Variable(n, integer=True)

    # Calculate dollar value target for each position
    dollar_target = capital * weights_target

    # Define the objective - minimize the absolute difference between actual dollar values and target dollar values
    objective = cp.Minimize(cp.sum(cp.abs(cp.multiply(x, prices) - dollar_target)))

    constraints = [
        x >= 0,
        cp.sum(cp.multiply(x, prices)) <= capital
    ]

    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.GLPK_MI)
    
    if prob.status != 'optimal':
        print(f"Warning: Optimization did not converge to optimal solution. Status: {prob.status}")
        return pd.DataFrame(columns=["ticker", "shares", "price", "value", "target_weight", "actual_weight"])
    
    # Output results
    x_opt = np.floor(x.value).astype(int)  # convert to integer
    total_invested = np.dot(x_opt, prices)
    cash_left = capital - total_invested
    print(f"Cash left uninvested: {cash_left}")

    result_df = pd.DataFrame({
        "ticker": tickers,
        "shares": x_opt,
        "price": prices,
        "value": x_opt * prices,
        "target_weight": weights_target,
        "actual_weight": np.where(total_invested > 0, (x_opt * prices) / total_invested, 0)
    })

    return result_df
