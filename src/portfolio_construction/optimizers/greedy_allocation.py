import pandas as pd


def greedy_allocation(tickers, prices, weights_target, capital=1000000):
    """
    Greedy algorithm for portfolio allocation.

    Parameters:
    tickers: List of ticker symbols
    prices: List of corresponding prices
    weights_target: List of target portfolio weights
    capital: Total capital to allocate (default: 1,000,000)

    Returns:
    DataFrame with allocation results
    """
    # Create dataframe from inputs
    allocation_data = {
        "ticker": tickers,
        "price": prices,
        "target_weight": weights_target,
    }
    df = pd.DataFrame(allocation_data)
    df = df.sort_values("target_weight", ascending=False)
    remaining_capital = capital
    df["target_dollars"] = capital * df["target_weight"]

    # Greedy allocation - calculate integer shares
    df["shares"] = df.apply(
        lambda row: (
            int(
                min(
                    row["target_dollars"] // row["price"],
                    remaining_capital // row["price"],
                )
            )
            if row["price"] > 0
            else 0
        ),
        axis=1,
    )

    # Update remaining capital after each allocation
    for idx, row in df.iterrows():
        shares = row["shares"]
        price = row["price"]
        value = shares * price
        remaining_capital -= value
        df.at[idx, "value"] = value

    # Calculate actual weights
    total_invested = df["value"].sum()
    if total_invested > 0:
        df["ActualWeight"] = df["value"] / total_invested
    else:
        df["ActualWeight"] = 0

    # Return results
    result_df = df[
        ["ticker", "shares", "price", "value", "target_weight", "ActualWeight"]
    ]
    return result_df


def linear_optimization(tickers, prices, weights_target, capital=1000000):
    """
    Simple linear optimization approach for portfolio allocation.
    Tries to get closer to optimal by doing multiple passes.

    Parameters:
    tickers: List of ticker symbols
    prices: List of corresponding prices
    weights_target: List of target portfolio weights
    capital: Total capital to allocate (default: 1,000,000)

    Returns:
    DataFrame with allocation results
    """
    # Initial allocation using greedy approach
    df = greedy_allocation(tickers, prices, weights_target, capital)

    # Get remaining capital
    total_invested = df["value"].sum()
    remaining_capital = capital - total_invested

    # Second pass: Distribute remaining capital
    if remaining_capital > 0:
        # Calculate weight error (target - actual)
        df["WeightError"] = df["target_weight"] - df["ActualWeight"]

        # Sort by weight error (underweight positions first)
        df = df.sort_values("WeightError", ascending=False)

        # Allocate remaining capital to reduce errors
        for idx, row in df.iterrows():
            if remaining_capital < row["price"] or row["price"] <= 0:
                continue

            additional_shares = int(remaining_capital // row["price"])
            if additional_shares > 0:
                df.at[idx, "shares"] += additional_shares
                df.at[idx, "value"] = df.at[idx, "shares"] * row["price"]
                remaining_capital -= additional_shares * row["price"]

    # Recalculate actual weights
    total_invested = df["value"].sum()
    if total_invested > 0:
        df["ActualWeight"] = df["value"] / total_invested
    else:
        df["ActualWeight"] = 0

    return df
