from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil
from src.data_access.sqllite_db_manager import TableNames
from src.portfolio_construction.optimizers.cvxpy_optimizer import cvx_optimizer
from src.portfolio_construction.optimizers.greedy_allocation import \
    greedy_allocation


@dataclass
class RebalanceData:
    strategy_name: str = None
    rebalance_date: date = None
    alpha_df: pd.DataFrame = None
    prices_df: pd.DataFrame = None
    rebalance_target_value: float = None


def create_rebalance_data(strategy_name, rebalance_date, alpha_df, prices_df, rebalance_target_value):
    return RebalanceData(
        strategy_name=strategy_name,
        rebalance_date=rebalance_date,
        alpha_df=alpha_df,
        prices_df=prices_df,
        rebalance_target_value=rebalance_target_value
    )


class RebalanceUtil:
    """Utility class for portfolio rebalancing operations."""

    @staticmethod
    def get_alpha_scores(strategy, start_date, end_date=None):
        table_name = TableNames.ALPHA_SCORES.value
        base_query = f"""
        SELECT *
        FROM {table_name}
        WHERE strategy_name = :strategy
        """

        params = {"strategy": strategy}
        conditions = []

        if start_date:
            conditions.append("date(date) >= date(:start_date)")
            params["start_date"] = start_date
        if end_date:
            conditions.append("date(date) <= date(:end_date)")
            params["end_date"] = end_date

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        stmt = text(base_query)
        df = DataAccessUtil.fetch_data_from_db(stmt, params)
        return df

    @staticmethod
    def get_aum_leverage_data(strategy_name, start_date, end_date=None):
        table_name = TableNames.AUM_LEVERAGE.value
        base_query = f"""
            SELECT date, strategy_name, aum, target_leverage,
            aum - LAG(aum, 1) OVER (PARTITION BY strategy_name ORDER BY date) AS in_out_flows,
            target_leverage - LAG(target_leverage, 1) OVER (PARTITION BY strategy_name ORDER BY date) AS leverage_change
            FROM {table_name}
            WHERE strategy_name = :strategy_name
        """

        params = {"strategy_name": strategy_name}
        conditions = []

        if start_date:
            conditions.append("date(date) >= date(:start_date)")
            params["start_date"] = start_date
        if end_date:
            conditions.append("date(date) <= date(:end_date)")
            params["end_date"] = end_date

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        stmt = text(base_query)
        df = DataAccessUtil.fetch_data_from_db(stmt, params)
        return df

    @staticmethod
    def get_new_portfolio_notional(aum_leverage_df, rebalance_date, current_pf_value, is_initial_rebalance=False):
        """Calculates new portfolio value based on AUM and leverage changes."""
        if not isinstance(rebalance_date, str):
            rebalance_date = pd.to_datetime(rebalance_date).strftime("%Y-%m-%d")

        aum_data = aum_leverage_df[aum_leverage_df['date'] == rebalance_date]

        if aum_data.empty:
            return current_pf_value

        current_leverage = aum_data['target_leverage'].values[0]
        if is_initial_rebalance:
            aum = aum_data['aum'].values[0]
            return aum * current_leverage
        else:
            # There are two components capital increase from second period onwards,
            # 1. First the leverage can be increased (or decreased)
            # 2. Second, new capital can be added (which in turn requires to be adjusted current target leverage)
            in_out_flows = pd.to_numeric(aum_data['in_out_flows'], errors='coerce').fillna(0).values[0]
            new_capital_inflows = current_leverage * in_out_flows
            leverage_change = pd.to_numeric(aum_data['leverage_change'], errors='coerce').fillna(0).values[0]

            current_portfolio_value_with_out_leverage = current_pf_value / (current_leverage - leverage_change)

            leverage_increase = current_leverage * current_portfolio_value_with_out_leverage
            return leverage_increase + new_capital_inflows


class RebalancePortfolio():

    def __init__(self, rebalance_data):
        self.rebalance_data = rebalance_data

    def rebalance_portfolio(self):
        """Rebalances portfolio using alpha scores and target values."""
        alpha_scores_df = self.rebalance_data.alpha_df
        prices_df = self.rebalance_data.prices_df
        rebalance_date = self.rebalance_data.rebalance_date
        rebalance_target_value = self.rebalance_data.rebalance_target_value
        strategy_name = self.rebalance_data.strategy_name

        if prices_df.empty or all(prices_df['value'] == 0):
            # No price data for the rebalance
            return pd.DataFrame()

        # Get unique trade directions(L/S) and get optimized portfolio.
        trade_directions = alpha_scores_df["trade_direction"].unique()
        results = []

        for direction in trade_directions:
            directional_target_value = rebalance_target_value / 2
            print(f"Optimizing {direction} positions...")
            direction_df = alpha_scores_df[alpha_scores_df["trade_direction"] == direction].copy()

            tickers = direction_df["ticker"].values
            weights_target = direction_df["weight"].values
            price_series = prices_df.set_index('ticker')['value']
            prices = price_series.reindex(tickers).fillna(0).values

            try:
                result_df = cvx_optimizer(tickers, prices, weights_target, directional_target_value)
            except Exception as e:
                print("Error occurred in CVX based optimization. Now trying the simple greedy approach.")
                print(f"The error is {str(e)}")
                result_df = greedy_allocation(tickers, prices, weights_target, directional_target_value)
            result_df["direction"] = direction
            if direction == "Short":
                result_df["shares"] = -1 * result_df["shares"]
            results.append(result_df)

        if len(results) > 1:
            result_df = pd.concat(results)
        elif len(results) == 1:
            result_df = results[0]
        else:
            result_df = pd.DataFrame()

        result_df = result_df.rename(columns={"price": "trade_open_price"})
        result_df["trade_open_date"] = rebalance_date
        selected_columns = ['trade_open_date', 'ticker', 'shares', 'trade_open_price', 'direction']
        result_df = result_df[selected_columns]
        result_df.loc[:, "trade_close_date"] = pd.NaT
        result_df.loc[:, "trade_close_price"] = np.nan
        result_df["strategy_name"] = strategy_name
        return result_df
