from datetime import datetime

import pandas as pd

from data_access.crud_util import DataAccessUtil
from data_access.sqllite_db_manager import TableNames, get_db_engine

# Create date range
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
# dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
dates = pd.date_range(
    start=start_date,
    end=end_date,
    freq='W-FRI'  # Weekly on Friday
)

STRATEGY_MOMROC = 'Mom_RoC'
STRATEGY_MINVOL = 'MinVol'


def create_MomRoc_strategy_aum_leverage_data():
    # Function to determine AUM
    def get_aum_mom_roc(date):
        if date <= datetime.strptime("2024-02-28", "%Y-%m-%d"):
            return 100_000_000  # 50_000_000
        elif date <= datetime.strptime("2024-06-30", "%Y-%m-%d"):
            return 100_000_000  # 75_000_000
        else:
            return 100_000_000

    # Function to determine Leverage
    def get_leverage_mom_roc(date):
        if date <= datetime.strptime("2024-03-31", "%Y-%m-%d"):
            return 2
        elif date <= datetime.strptime("2024-07-31", "%Y-%m-%d"):
            return 3
        else:
            return 4

    # Initialize empty lists
    all_dates = []
    all_strategies = []
    all_aums = []
    all_target_leverages = []

    # Use the provided functions to fill data
    for date in dates:
        strategy = STRATEGY_MOMROC
        aum = get_aum_mom_roc(date)
        leverage = get_leverage_mom_roc(date)

        all_dates.append(date)
        all_strategies.append(strategy)
        all_aums.append(aum)
        all_target_leverages.append(leverage)

    # Create the DataFrame
    df = pd.DataFrame({
        'date': all_dates,
        'strategy_name': all_strategies,
        'aum': all_aums,
        'target_leverage': all_target_leverages
    })

    # Ensure date is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    return df


def create_MinVol_strategy_aum_leverage_data():
    # Function to determine AUM
    def get_aum_MinVol(date):
        if date <= datetime.strptime("2024-05-31", "%Y-%m-%d"):
            return 50_000_000
        elif date <= datetime.strptime("2024-09-30", "%Y-%m-%d"):
            return 75_000_000
        else:
            return 100_000_000

    # Function to determine Leverage
    def get_leverage_MinVol(date):
        if date <= datetime.strptime("2024-03-31", "%Y-%m-%d"):
            return 2
        else:
            return 4

    # Initialize empty lists
    all_dates = []
    all_strategies = []
    all_aums = []
    target_leverage = []

    # Use the provided functions to fill data
    for date in dates:
        strategy = STRATEGY_MINVOL
        aum = get_aum_MinVol(date)
        leverage = get_leverage_MinVol(date)

        all_dates.append(date)
        all_strategies.append(strategy)
        all_aums.append(aum)
        target_leverage.append(leverage)

    # Create the DataFrame
    df = pd.DataFrame({
        'date': all_dates,
        'strategy_name': all_strategies,
        'aum': all_aums,
        'target_leverage': target_leverage
    })

    # Ensure date is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    return df


if __name__ == "__main__":
    aum_leverage_data_mom_roc = create_MomRoc_strategy_aum_leverage_data()
    aum_leverage_data_min_vol = create_MinVol_strategy_aum_leverage_data()

    engine = get_db_engine()
    aum_lev_tbl = TableNames.AUM_LEVERAGE.value
    DataAccessUtil.store_dataframe_to_table(dataframe=aum_leverage_data_min_vol, table_name=aum_lev_tbl)
    DataAccessUtil.store_dataframe_to_table(dataframe=aum_leverage_data_mom_roc, table_name=aum_lev_tbl)
