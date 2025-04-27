from src.data_access.schemas import UniverseSpec
from src.strategy.min_vol.min_vol import MinVolSignal, MinVolSignalData


def test_min_vol_signal_initialization():
    # Create sample data
    spec = UniverseSpec(
        universe='test',
        start_date='2023-01-01',
        end_date='2023-01-31'
    )
    
    signal = MinVolSignal(spec)
    assert signal.spec == spec
    assert isinstance(signal.min_vol_data, MinVolSignalData) 