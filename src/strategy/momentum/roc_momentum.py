from dataclasses import dataclass, field

import pandas as pd

from src.data_access.prices import PriceDataFetcher
from src.data_access.schemas import UniverseSpec
from src.data_access.sqllite_db_manager import get_db_engine
from src.strategy.strategy import Strategy
from src.strategy.strategy_utils import build_and_store_signal

SIGNAL_NAME = "Mom_RoC"


@dataclass
class RoCSignalData:
    spec: UniverseSpec
    price_data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.price_data = PriceDataFetcher.get_price_data(spec=self.spec, engine=get_db_engine())


class RocSignal(Strategy):
    def __init__(self, spec: UniverseSpec) -> None:
        super().__init__(spec, SIGNAL_NAME)
        self.roc_data = RoCSignalData(spec)

    def calculate_signal_scores(self) -> pd.DataFrame:
        df_raw = self.roc_data.price_data

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


if __name__ == "__main__":
    start_date = '2023-09-01'
    end_date = '2025-01-31'
    spec = UniverseSpec(
        universe='sp500',
        start_date=start_date,
        end_date=end_date
    )

    strategy = RocSignal(spec)
    build_and_store_signal(strategy, start_date, end_date)
