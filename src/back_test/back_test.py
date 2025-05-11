from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.back_test.create_aggregated_fund_trades import \
    create_aggregated_fund_trades
from src.data_access.crud_util import DataAccessUtil
from src.data_access.prices import PriceDataFetcher
from src.data_access.schemas import UniverseSpec
from src.data_access.sqllite_db_manager import TableNames
from src.data_access.trade_booking import update_trades
from src.rebalance.rebalance_portfolio import (RebalancePortfolio,
                                               RebalanceUtil,
                                               create_rebalance_data)


@dataclass
class BackTestData:
    strategy_name: str
    univ_spec: UniverseSpec
    start_date: date
    end_date: date
    aum_leverage_df: pd.DataFrame = None
    alpha_scores_df: pd.DataFrame = None
    price_history_df: pd.DataFrame = None
    # Create instance with the required datasets


def create_backtest_data(strategy_name, start_date, end_date):
    # Initialize universe specification and fetch required datasets
    univ_spec = UniverseSpec("SP500", start_date, end_date)
    price_history_df = PriceDataFetcher.get_price_data(univ_spec)
    alpha_scores_df = RebalanceUtil.get_alpha_scores(strategy_name, start_date, end_date)
    aum_leverage_df = RebalanceUtil.get_aum_leverage_data(strategy_name, start_date, end_date)

    # Create and return the BackTestData instance
    return BackTestData(
        strategy_name=strategy_name,
        univ_spec=univ_spec,
        start_date=start_date,
        end_date=end_date,
        aum_leverage_df=aum_leverage_df,
        alpha_scores_df=alpha_scores_df,
        price_history_df=price_history_df
    )


class BackTestUtil:

    @staticmethod
    def get_previous_rebalance_data(strategy_name, rebalance_date):
        table_name = TableNames.TRADE_BOOKING.value

        # Base query definition
        base_query = f"""
        SELECT *
        FROM {table_name}
        WHERE trade_open_date = (
            SELECT MAX(trade_open_date)
            FROM {table_name}
            WHERE date(trade_open_date) < date(:rebalance_date)
            AND strategy_name = :strategy_name
        )
        AND strategy_name = :strategy_name
        """

        # Initialize parameters dictionary
        params = {
            "rebalance_date": str(pd.Timestamp(rebalance_date).date()),
            "strategy_name": strategy_name
        }

        conditions = []

        # Append conditions to the base query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        stmt = text(base_query)
        df = DataAccessUtil.fetch_data_from_db(stmt, params)
        return df

    @staticmethod
    def fill_trade_closing_prices(previous_rebal_trades_df, trade_closing_prices_df, rebalance_date):
        rebalance_date_formatted = pd.Timestamp(rebalance_date)

        prev_rebalance_df = previous_rebal_trades_df.merge(trade_closing_prices_df, on='ticker', how='left')
        prev_rebalance_df['trade_close_price'] = prev_rebalance_df['value']
        prev_rebalance_df.drop('value', axis=1, inplace=True)

        prev_rebalance_df['trade_close_date'] = rebalance_date_formatted
        return prev_rebalance_df


class BackTest:
    def __init__(self, backtest_data):
        # Store the backtest_data in the instance
        self.backtest_data = backtest_data

    def run_backtest(self):
        # Extract required data items from the BackTestData object
        backtest_data = self.backtest_data
        strategy_name = backtest_data.strategy_name
        price_history = backtest_data.price_history_df
        alpha_scores_df = backtest_data.alpha_scores_df
        aum_leverage_df = backtest_data.aum_leverage_df

        if alpha_scores_df.empty:
            print(" No Alpha scores for this strategy and for given dates.")
            return

        unique_dates = np.sort(alpha_scores_df['date'].unique())
        initial_rebalance_date = unique_dates[0]

        for rebalance_date in unique_dates:
            print(rebalance_date)
            if pd.to_datetime(rebalance_date).date() == pd.to_datetime("2024-11-22").date():
                print(rebalance_date)

            prev_rebalance_trade_data = BackTestUtil.get_previous_rebalance_data(strategy_name, rebalance_date)
            prev_rebalance_tickers = np.unique(prev_rebalance_trade_data['ticker'])
            current_rebalance_alpha_scores_df = alpha_scores_df[alpha_scores_df['date'] == rebalance_date]
            current_rebalance_tickers = np.unique(current_rebalance_alpha_scores_df['ticker'])

            prev_rebalance_closing_prices = price_history[price_history['date'].isin([rebalance_date]) &
                                                          price_history['ticker'].isin(prev_rebalance_tickers)]
            new_rebalance_opening_prices = price_history[price_history['date'].isin([rebalance_date]) &
                                                         price_history['ticker'].isin(current_rebalance_tickers)]

            closed_trades_df = BackTestUtil.fill_trade_closing_prices(prev_rebalance_trade_data,
                                                                      prev_rebalance_closing_prices, rebalance_date)
            closing_value_prev_rebal = np.nansum(
                (closed_trades_df['trade_close_price'] * abs(closed_trades_df['shares'])))

            new_notional = RebalanceUtil.get_new_portfolio_notional(aum_leverage_df, rebalance_date,
                                                                    closing_value_prev_rebal,
                                                                    initial_rebalance_date == rebalance_date)

            alpha_scores_current_rebalance_df = alpha_scores_df[alpha_scores_df['date'] == rebalance_date]

            rebalance_data = create_rebalance_data(strategy_name, rebalance_date, alpha_scores_current_rebalance_df,
                                                   new_rebalance_opening_prices, new_notional)

            rb = RebalancePortfolio(rebalance_data)
            new_portfolio = rb.rebalance_portfolio()

            update_trades(closed_trades_df)
            update_trades(new_portfolio)
        else:
            # Close the last rebalance trades (as its back test it can't have opened trades).
            prev_rebalance_closing_prices = price_history[price_history['date'].isin([rebalance_date]) &
                                                          price_history['ticker'].isin(current_rebalance_tickers)]
            closed_trades_df = BackTestUtil.fill_trade_closing_prices(new_portfolio,
                                                                      prev_rebalance_closing_prices, rebalance_date)
            closed_trades_df['trade_close_date'] = rebalance_date
            update_trades(closed_trades_df)


if __name__ == "__main__":
    list_of_strategies = ["MinVol", "Mom_RoC"]
    start_date, end_date = "2024-01-01", "2025-01-15"
    for strategy in list_of_strategies:
        back_test_data = create_backtest_data(strategy, start_date, end_date)
        bt = BackTest(back_test_data)
        bt.run_backtest()

    # Finally create the aggregated fund trades by aggregating all trades as part of "AggregatedFund"
    # This is simplification for the purpose of building dashboard (choice between data duplication vs simplicity)
    create_aggregated_fund_trades()
