from typing import NoReturn

import pandas as pd

from src.data_access.crud_util import DataAccessUtil
from src.data_access.sqllite_db_manager import TableNames
from src.portfolio_construction.optimizers.create_portfolio_weights import \
    construct_portfolio_weights
from src.strategy.strategy import Strategy


def build_and_store_signal(strategy: Strategy) -> NoReturn:
    """
    Build and store signal for any strategy that implements the Strategy interface
    
    Args:
        strategy: Instance of a class implementing Strategy interface
    """
    signal_df = strategy.calculate_signal_scores()
    portfolio_weights_df = construct_portfolio_weights(signal_df, strategy.strategy_name)

    print(f"{strategy.strategy_name} signal:")
    print(portfolio_weights_df.head(3))
    
    alpha_scores_tbl = TableNames.ALPHA_SCORES.value

    all_fridays = pd.date_range(
        start=strategy.spec.start_date,
        end=strategy.spec.end_date,
        freq='W-FRI'  # Weekly frequency on Friday
    )

    portfolio_weights_df['date'] = pd.to_datetime(portfolio_weights_df['date'])
    resampled_df = portfolio_weights_df[portfolio_weights_df['date'].isin(all_fridays)]

    # Delete existing records using parameterized query
    delete_query = """
        DELETE FROM {table_name} 
        WHERE strategy_name = :strategy_name 
        AND date >= date(:start_date) 
        AND date <= date(:end_date)
    """.format(table_name=alpha_scores_tbl)

    params = {
        'strategy_name': strategy.strategy_name,
        'start_date': strategy.spec.start_date,
        'end_date': strategy.spec.end_date
    }

    DataAccessUtil.execute_statement(delete_query, params=params)
    DataAccessUtil.store_dataframe_to_table(
        dataframe=resampled_df,
        table_name=alpha_scores_tbl,
        index=False
    ) 