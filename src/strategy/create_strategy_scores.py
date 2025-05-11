from src.data_access.schemas import UniverseSpec
from src.strategy.min_vol.min_vol import MinVolSignal
from src.strategy.momentum.roc_momentum import RocSignal
from src.strategy.strategy_utils import build_and_store_signal

if __name__ == "__main__":
    start_date = '2023-09-01'
    end_date = '2025-01-31'
    spec = UniverseSpec(
        universe='sp500',
        start_date=start_date,
        end_date=end_date
    )

    strategies = [RocSignal(spec), MinVolSignal(spec)]
    for strategy in strategies:
        build_and_store_signal(strategy)
