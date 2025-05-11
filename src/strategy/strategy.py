from abc import ABC, abstractmethod

import pandas as pd

from src.data_access.schemas import UniverseSpec


class Strategy(ABC):
    def __init__(self, spec: UniverseSpec, strategy_name: str) -> None:
        self.spec = spec
        self.strategy_name = strategy_name

    @abstractmethod
    def calculate_signal_scores(self) -> pd.DataFrame:
        """Calculate signal scores for the strategy"""
        pass
