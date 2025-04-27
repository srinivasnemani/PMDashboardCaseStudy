import numpy as np
import pandas as pd


def construct_portfolio_weights(signal_df, strategy_name, top_n=25):
    """
    Construct portfolio weights from signal data.
    
    Parameters:
    signal_df (pd.DataFrame): DataFrame with signals, index as dates and columns as tickers
    strategy_name (str): Name of the strategy
    top_n (int): Number of top/bottom stocks to select
    
    Returns:
    pd.DataFrame: DataFrame with weights and trade directions
    """
    ls_trade_list = []
    
    # Ensure we have enough assets for meaningful long/short positions
    min_assets = max(2, top_n)
    
    for date, row in signal_df.iterrows():
        valid_scores = row.dropna()
        
        # For single asset case, just go long
        if len(valid_scores) == 1:
            df_long = pd.DataFrame({
                "date": date,
                "trade_direction": "Long",
                "ticker": valid_scores.index,
                "alpha_score": valid_scores.values,
                "weight": [1.0]
            })
            ls_trade_list.append(df_long)
            continue
            
        # Skip if we don't have enough valid scores for balanced long/short
        if len(valid_scores) < min_assets:
            continue

        # Sort by absolute values but keep original signs
        abs_scores = valid_scores.abs()
        sorted_indices = abs_scores.sort_values(ascending=False).index
        sorted_scores = valid_scores[sorted_indices]
        
        n_assets = min(top_n, len(sorted_scores) // 2)  # Ensure balanced long/short
        
        if n_assets == 0:
            continue
            
        # Select top and bottom assets by absolute value
        top_scores = sorted_scores.iloc[:n_assets]
        bottom_scores = sorted_scores.iloc[-n_assets:]
        
        # Determine which scores go to long and short based on sign
        if all(sorted_scores < 0):
            # For all negative scores, reverse the direction
            long_scores = bottom_scores
            short_scores = top_scores
        else:
            long_scores = top_scores
            short_scores = bottom_scores

        # Skip if all scores are zero
        if long_scores.abs().sum() == 0 and short_scores.abs().sum() == 0:
            continue

        # Calculate weights ensuring they sum to 1
        long_weights = np.zeros(len(long_scores))
        short_weights = np.zeros(len(short_scores))

        if long_scores.abs().sum() != 0:
            long_weights = np.abs(long_scores.values) / np.abs(long_scores).sum()
        if short_scores.abs().sum() != 0:
            short_weights = np.abs(short_scores.values) / np.abs(short_scores).sum()

        df_long = pd.DataFrame({
            "date": date,
            "trade_direction": "Long",
            "ticker": long_scores.index,
            "alpha_score": long_scores.values,
            "weight": long_weights,
        })

        df_short = pd.DataFrame({
            "date": date,
            "trade_direction": "Short",
            "ticker": short_scores.index,
            "alpha_score": short_scores.values,
            "weight": short_weights,
        })

        ls_trade_list.append(df_long)
        ls_trade_list.append(df_short)

    if not ls_trade_list:
        return pd.DataFrame(columns=["date", "trade_direction", "ticker", "alpha_score", "weight", "strategy_name"])

    ls_trades_df = pd.concat(ls_trade_list, ignore_index=True)
    ls_trades_df.sort_values(by=["date", "trade_direction", "ticker"], inplace=True)
    ls_trades_df["strategy_name"] = strategy_name
    ls_trades_df.reset_index(drop=True, inplace=True)

    return ls_trades_df
