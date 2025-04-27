import pandas as pd

from src.data_access.trade_booking import get_trade_and_sec_master_data


def calcualte_exposures_by_direction_net_total(df: pd.DataFrame):
    df['exposure'] = df['shares'] * df['trade_open_price']

    exposures_by_direction = (
        df.groupby(['gics_sector', 'direction'])['exposure']
        .sum()
        .reset_index()
    )

    total_gross_exposure = exposures_by_direction['exposure'].abs().sum()

    exposures_by_direction['exposure_pct'] = (
            exposures_by_direction['exposure'].abs() / total_gross_exposure * 100
    )

    exposures_pivot = (
        exposures_by_direction
        .pivot(index='gics_sector', columns='direction', values='exposure')
        .fillna(0)
    )

    # Ensure both Long and Short columns exist for further calculations
    if 'Long' not in exposures_pivot.columns:
        exposures_pivot['Long'] = 0
    if 'Short' not in exposures_pivot.columns:
        exposures_pivot['Short'] = 0

    exposures_pivot['absolute_exposure_usd'] = exposures_pivot['Long'].abs() + exposures_pivot['Short'].abs()
    exposures_pivot['net_exposure_usd'] = exposures_pivot['Long'] + exposures_pivot['Short']

    total_absolute_exposure = exposures_pivot['absolute_exposure_usd'].sum()

    exposures_pivot['absolute_exposure_pct'] = (
            exposures_pivot['absolute_exposure_usd'] / total_absolute_exposure * 100
    )
    exposures_pivot['net_exposure_pct'] = (
            exposures_pivot['net_exposure_usd'] / total_absolute_exposure * 100
    )

    exposures_net_total = exposures_pivot.reset_index()

    return exposures_by_direction, exposures_net_total


def get_exposures_by_direction_net_total(strategy_name, rebalance_date):
    trade_data_df = get_trade_and_sec_master_data(strategy_name, start_date=rebalance_date, end_date=rebalance_date)
    [exposures_by_direction, exposures_net_total] = calcualte_exposures_by_direction_net_total(trade_data_df)
    return [exposures_by_direction, exposures_net_total]


if __name__ == "__main__":
    strategy_name = "MinVol"
    date_val = "2024-07-26"
    trade_data_df = get_trade_and_sec_master_data(strategy_name, start_date=date_val, end_date=date_val)
    trade_data_df.to_clipboard()
    [df1, df2] = calcualte_exposures_by_direction_net_total(trade_data_df)
    print(df1)
