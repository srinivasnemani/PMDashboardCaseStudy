from dataclasses import dataclass, field

import pandas as pd
from src.data_access.crud_util import DataAccessUtil
from src.data_access.prices import PriceDataFetcher
from src.data_access.schemas import UniverseSpec
from src.data_access.sqllite_db_manager import TableNames, get_db_engine
from src.portfolio_construction.optimizers.create_portfolio_weights import \
    construct_portfolio_weights

SIGNAL_NAME = "MinVol"


@dataclass
class MinVolSignalData:
    spec: UniverseSpec
    price_data: pd.DataFrame = field(init=False)
    benchmark_data: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.price_data = PriceDataFetcher.get_price_data(spec=self.spec, engine=get_db_engine())
        self.benchmark_data = PriceDataFetcher.get_benchmark_data(spec=self.spec, engine=get_db_engine())


class MinVolSignal:
    def __init__(self, spec: UniverseSpec):
        self.spec = spec
        self.min_vol_data = MinVolSignalData(spec)

    def calculate_signal_scores(self, min_vol_data: MinVolSignalData) -> pd.DataFrame:
        stock_df_raw = min_vol_data.price_data
        benchmark_df_raw = min_vol_data.benchmark_data

        stock_px_df = stock_df_raw.pivot(index="date", columns="ticker", values="value")
        benchmark_px_df = benchmark_df_raw.pivot(index="date", columns="ticker", values="value")

        stock_px_df = stock_px_df.asfreq('B').ffill()
        benchmark_px_df = benchmark_px_df.asfreq('B').ffill()

        stock_returns = stock_px_df.pct_change()
        benchmark_returns = benchmark_px_df.pct_change()

        stock_vol_10d = stock_returns.rolling(window=10).std()
        benchmark_vol_10d = benchmark_returns.rolling(window=10).std()

        # Ensure single benchmark and broadcast to match stock universe
        if benchmark_vol_10d.shape[1] != 1:
            raise ValueError("Expected exactly one benchmark ticker.")
        benchmark_vol_series = benchmark_vol_10d.iloc[:, 0]

        benchmark_vol_aligned = pd.concat(
            [benchmark_vol_series] * stock_vol_10d.shape[1],
            axis=1
        )
        benchmark_vol_aligned.columns = stock_vol_10d.columns

        # Relative volatility: lower stock volatility relative to benchmark
        relative_vol = stock_vol_10d / benchmark_vol_aligned

        # Invert: lower relative volatility → better stock
        signal_df = -relative_vol
        signal_df = signal_df.dropna(how='all')

        return signal_df


def demo_build_signal():
    spec = UniverseSpec(
        universe='sp500',
        start_date='2023-09-01',
        end_date='2025-01-31'
    )

    signal = MinVolSignal(spec)
    rel_vol_signal_df = signal.calculate_signal_scores(signal.min_vol_data)
    portfolio_weights_df = construct_portfolio_weights(rel_vol_signal_df, SIGNAL_NAME)

    print("Relative volatility signal (lower volatility relative to benchmark is better):")
    print(portfolio_weights_df.head(3))
    alpha_scores_tbl = TableNames.ALPHA_SCORES.value

    start_date = '2024-01-01'
    end_date = '2024-12-31'
    all_fridays = pd.date_range(
        start=start_date,
        end=end_date,
        freq='W-FRI'  # Weekly frequency on Friday
    )
    # portfolio_weights_df.index = pd.to_datetime(portfolio_weights_df.index)
    resampled_df = portfolio_weights_df[portfolio_weights_df['date'].isin(all_fridays)]
    # resampled_df = resampled_df.reindex(all_fridays, method='ffill')
    DataAccessUtil.store_dataframe_to_table(dataframe=resampled_df, table_name=alpha_scores_tbl)


# def run_backtest_min_vol():
#     get_aum_leverage_data('Mom_RoC', '2024-01-01', end_date=None)

if __name__ == "__main__":
    demo_build_signal()
    # run_backtest_min_vol()
