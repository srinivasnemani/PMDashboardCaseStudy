from dataclasses import dataclass, field

import pandas as pd

from src.data_access.prices import PriceDataFetcher
from src.data_access.schemas import UniverseSpec
from src.data_access.sqllite_db_manager import get_db_engine
from src.strategy.strategy import Strategy
from src.strategy.strategy_utils import build_and_store_signal

SIGNAL_NAME = "MinVol"


@dataclass
class MinVolSignalData:
    spec: UniverseSpec
    price_data: pd.DataFrame = field(init=False)
    benchmark_data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.price_data = PriceDataFetcher.get_price_data(
            spec=self.spec, engine=get_db_engine()
        )
        self.benchmark_data = PriceDataFetcher.get_benchmark_data(
            spec=self.spec, engine=get_db_engine()
        )


class MinVolSignal(Strategy):
    def __init__(self, spec: UniverseSpec) -> None:
        super().__init__(spec, SIGNAL_NAME)
        self.min_vol_data = MinVolSignalData(spec)

    def calculate_signal_scores(self) -> pd.DataFrame:
        stock_df_raw = self.min_vol_data.price_data
        benchmark_df_raw = self.min_vol_data.benchmark_data

        stock_px_df = stock_df_raw.pivot(index="date", columns="ticker", values="value")
        benchmark_px_df = benchmark_df_raw.pivot(
            index="date", columns="ticker", values="value"
        )

        stock_px_df = stock_px_df.asfreq("B").ffill()
        benchmark_px_df = benchmark_px_df.asfreq("B").ffill()

        stock_returns = stock_px_df.pct_change()
        benchmark_returns = benchmark_px_df.pct_change()

        stock_vol_10d = stock_returns.rolling(window=10).std()
        benchmark_vol_10d = benchmark_returns.rolling(window=10).std()

        # Ensure single benchmark and broadcast to match stock universe
        if benchmark_vol_10d.shape[1] != 1:
            raise ValueError("Expected exactly one benchmark ticker.")
        benchmark_vol_series = benchmark_vol_10d.iloc[:, 0]

        benchmark_vol_aligned = pd.concat(
            [benchmark_vol_series] * stock_vol_10d.shape[1], axis=1
        )
        benchmark_vol_aligned.columns = stock_vol_10d.columns

        # Relative volatility: lower stock volatility relative to benchmark
        relative_vol = stock_vol_10d / benchmark_vol_aligned

        # Invert: lower relative volatility → better stock
        signal_df = -relative_vol
        signal_df = signal_df.dropna(how="all")

        return signal_df


if __name__ == "__main__":
    start_date = "2023-09-01"
    end_date = "2025-01-31"
    spec = UniverseSpec(universe="sp500", start_date=start_date, end_date=end_date)

    strategy = MinVolSignal(spec)
    build_and_store_signal(strategy)
