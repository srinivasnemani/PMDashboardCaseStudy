from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from src.data_access.crud_util import DataAccessUtil
from src.data_access.prices import PriceDataFetcher
from src.data_access.schemas import UniverseSpec
from src.data_access.sqllite_db_manager import TableNames, get_db_engine
from src.portfolio_construction.optimizers.create_portfolio_weights import \
    construct_portfolio_weights

SIGNAL_NAME = "Mom_RoC"


@dataclass
class RoCSignalData:
    spec: UniverseSpec
    price_data: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.price_data = PriceDataFetcher.get_price_data(spec=self.spec, engine=get_db_engine())


class RocSignal:
    def __init__(self, spec: UniverseSpec):
        self.spec = spec
        self.roc_data = RoCSignalData(spec)

    def calculate_signal_scores(self, roc_data: RoCSignalData) -> pd.DataFrame:
        df_raw = roc_data.price_data

        # Step 2: Pivot to wide format with dates as rows, tickers as columns
        px_last_df = df_raw.pivot(index="date", columns="ticker", values="value")

        # Step 3: Sort index and columns
        px_last_df.sort_index(inplace=True)
        px_last_df = px_last_df[sorted(px_last_df.columns)]

        # Step 4: Fill missing weekdays, apply 5-day moving average
        df_daily_5d = px_last_df.asfreq('B').ffill().rolling(window=5, min_periods=1).mean()

        # Step 5: Resample to weekly (Friday close)
        df_weekly = df_daily_5d.resample('W-FRI').last()

        # Step 6: Calculate 1w and 3w average RoC
        roc_1w = df_weekly.pct_change(periods=1)
        roc_3w = df_weekly.pct_change(periods=3) / 3

        # Step 7: Compute momentum acceleration
        roc_diff = roc_1w - roc_3w
        roc_diff = roc_diff[sorted(roc_diff.columns)]
        roc_diff.sort_index(inplace=True)

        return roc_diff


def demo_run():
    spec = UniverseSpec(
        universe='sp500',
        start_date='2023-11-01',
        end_date='2025-01-31'
    )

    signal = RocSignal(spec)
    roc_diff_df = signal.calculate_signal_scores(signal.roc_data)
    portfolio_weights_df = construct_portfolio_weights(roc_diff_df, SIGNAL_NAME)

    print("Relative volatility signal (lower volatility relative to benchmark is better):")
    print(portfolio_weights_df.shape)

    print("Momentum acceleration (1w - 3w RoC) for 2024:")
    # print(roc_diff_df)
    table_name = TableNames.ALPHA_SCORES.value
    DataAccessUtil.store_dataframe_to_table(portfolio_weights_df, table_name, if_exists='append', index=False)


if __name__ == "__main__":
    demo_run()
