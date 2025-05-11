import math

import pandas as pd
import pytest

from src.analytics.risk_attributions import RiskFactorAttributions


class MockRiskModel:
    def __init__(self):
        self.factor_exposures = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
                "ticker": ["AAPL", "MSFT"],
                "factor1": [0.5, 0.3],
                "factor2": [0.2, 0.4],
            }
        )
        self.factor_names = ["factor1", "factor2"]
        self.factor_covariance = pd.DataFrame(
            {"factor1": [0.04, 0.02], "factor2": [0.02, 0.09]},
            index=["factor1", "factor2"],
        )
        self.sp_risk_residuals = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
                "ticker": ["AAPL", "MSFT"],
                "specific_risk": [0.1, 0.15],
            }
        )


def create_sample_trade_data():
    return pd.DataFrame(
        {
            "ticker": ["AAPL", "MSFT"],
            "shares": [100, 200],
            "trade_open_price": [150.0, 200.0],
            "trade_close_price": [160.0, 210.0],
            "trade_open_date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "direction": ["Long", "Long"],
        }
    )


@pytest.fixture
def risk_attributions():
    trade_data = create_sample_trade_data()
    risk_model = MockRiskModel()
    return RiskFactorAttributions(trade_data, risk_model)


def test_compute_factor_pnl_attribution(risk_attributions):
    # Test case 1: Basic PnL attribution
    result = risk_attributions.compute_factor_pnl_attribution()

    assert isinstance(result, pd.DataFrame)
    assert "factor_pnl_usd" in result.columns
    assert "factor_exposure_pct" in result.columns
    assert "pnl_contribution_pct" in result.columns
    assert abs(result["pnl_contribution_pct"].sum() - 1.0) < 1e-10

    # Test case 2: PnL attribution with short trades
    trade_data = create_sample_trade_data()
    trade_data["direction"] = ["Short", "Short"]
    risk_model = MockRiskModel()
    risk_attributions_short = RiskFactorAttributions(
        trade_data, risk_model, trade_direction="SHORT"
    )
    result_short = risk_attributions_short.compute_factor_pnl_attribution()

    assert isinstance(result_short, pd.DataFrame)
    assert len(result_short) > 0


def test_compute_portfolio_risk_decomposition(risk_attributions):
    # Test case 1: Basic risk decomposition
    result = risk_attributions.compute_portfolio_risk_decomposition()

    assert isinstance(result, pd.DataFrame)
    assert "Factor Risk (Annualized Variance)" in result.columns
    assert "Specific Risk (Annualized Variance)" in result.columns
    assert "Total Risk (Annualized Variance)" in result.columns
    assert "Factor Risk (Annualized Vol)" in result.columns
    assert "Specific Risk (Annualized Vol)" in result.columns
    assert "Total Risk (Annualized Vol)" in result.columns
    assert "Factor Risk Contribution %" in result.columns
    assert "Specific Risk Contribution %" in result.columns
    # The sum of contributions should be close to 1.0
    assert abs(result["Factor Risk Contribution %"].iloc[0] + result["Specific Risk Contribution %"].iloc[0] - 1.0) < 1e-10

    # Test case 2: Risk decomposition with filtered trades
    trade_data = create_sample_trade_data()
    trade_data = trade_data[trade_data["ticker"] == "AAPL"]
    risk_model = MockRiskModel()
    risk_attributions_filtered = RiskFactorAttributions(trade_data, risk_model)
    result_filtered = risk_attributions_filtered.compute_portfolio_risk_decomposition()

    assert isinstance(result_filtered, pd.DataFrame)
    assert len(result_filtered) == 1
    assert "Factor Risk (Annualized Variance)" in result_filtered.columns
    assert "Specific Risk (Annualized Variance)" in result_filtered.columns
    assert "Total Risk (Annualized Variance)" in result_filtered.columns
    assert "Factor Risk (Annualized Vol)" in result_filtered.columns
    assert "Specific Risk (Annualized Vol)" in result_filtered.columns
    assert "Total Risk (Annualized Vol)" in result_filtered.columns
    assert "Factor Risk Contribution %" in result_filtered.columns
    assert "Specific Risk Contribution %" in result_filtered.columns
    assert abs(result_filtered["Factor Risk Contribution %"].iloc[0] + result_filtered["Specific Risk Contribution %"].iloc[0] - 1.0) < 1e-10


def test_compute_full_risk_decomposition(risk_attributions):
    # Test case 1: Basic full risk decomposition
    result = risk_attributions.compute_full_risk_decomposition()

    assert isinstance(result, pd.DataFrame)
    assert "Factor" in result.columns
    assert "Risk Contribution" in result.columns
    assert "Contribution %" in result.columns
    # Contribution % should sum to 100 (with a small tolerance for floating point error)
    # Exclude the "Total" row when checking the sum
    assert math.isclose(result[result["Factor"] != "Total"]["Contribution %"].sum(), 100.0, rel_tol=1e-4, abs_tol=1e-4)

    # Test case 2: Full risk decomposition with specific risk
    trade_data = create_sample_trade_data()
    risk_model = MockRiskModel()
    risk_model.sp_risk_residuals["specific_risk"] = [0.2, 0.3]  # Higher specific risk
    risk_attributions_high_specific = RiskFactorAttributions(trade_data, risk_model)
    result_high_specific = (
        risk_attributions_high_specific.compute_full_risk_decomposition()
    )

    assert isinstance(result_high_specific, pd.DataFrame)
    assert "Specific Risk" in result_high_specific["Factor"].values


def test_compute_all_factor_attributions(risk_attributions):
    # Test case 1: Basic all attributions
    result = risk_attributions.compute_all_factor_attributions()

    assert isinstance(result, dict)
    assert "factor_pnl_attribution" in result
    assert "portfolio_risk_decomposition" in result
    assert "full_risk_decomposition" in result

    # Test case 2: All attributions with single trade
    trade_data = create_sample_trade_data().iloc[:1]  # Take only first trade
    risk_model = MockRiskModel()
    risk_attributions_single = RiskFactorAttributions(trade_data, risk_model)
    result_single = risk_attributions_single.compute_all_factor_attributions()

    assert isinstance(result_single, dict)
    assert all(
        key in result_single
        for key in [
            "factor_pnl_attribution",
            "portfolio_risk_decomposition",
            "full_risk_decomposition",
        ]
    )
