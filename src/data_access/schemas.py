from dataclasses import dataclass
from typing import List, Optional, Union

import pandas as pd


@dataclass
class UniverseSpec:
    universe: str = 'sp500'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    day_frequency: Optional[str] = None


@dataclass
class RiskModel:
    date: Union[str, pd.Timestamp]
    factor_names: List[str]
    factor_exposures: pd.DataFrame
    factor_covariance: pd.DataFrame
    sp_risk_residuals: pd.DataFrame
