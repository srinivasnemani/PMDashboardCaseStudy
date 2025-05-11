import pandas as pd
import pytest

from src.analytics.back_test_summary import (
    BackTestSummaryAnalytics,
    BackTestSummaryAnalyticsData,
)


def create_sample_data(
    returns, benchmark_returns=None, risk_free_rate=None, trading_days=252
):
    """Helper function to create sample data for testing."""
    dates = pd.date_range(start="2020-01-01", periods=len(returns), freq="D")
    data = pd.DataFrame({"date": dates, "portfolio_returns": returns})

    if benchmark_returns is not None:
        data["benchmark_returns"] = benchmark_returns
    if risk_free_rate is not None:
        data["risk_free_rate"] = risk_free_rate

    return BackTestSummaryAnalyticsData(data=data, trading_days_per_year=trading_days)


class TestBackTestSummaryAnalyticsData:
    def test_initialization_with_required_columns(self):
        """Test initialization with required columns."""
        data = pd.DataFrame(
            {
                "date": pd.date_range(start="2020-01-01", periods=5),
                "portfolio_returns": [0.01, 0.02, -0.01, 0.03, 0.02],
            }
        )
        backtest_data = BackTestSummaryAnalyticsData(data=data)
        assert "portfolio_returns" in backtest_data.data.columns
        assert "risk_free_rate" in backtest_data.data.columns
        assert "benchmark_returns" in backtest_data.data.columns

    def test_missing_required_column(self):
        """Test initialization with missing required column."""
        data = pd.DataFrame({"date": pd.date_range(start="2020-01-01", periods=5)})
        with pytest.raises(ValueError):
            BackTestSummaryAnalyticsData(data=data)

    def test_date_index_conversion(self):
        """Test date column conversion to index."""
        data = pd.DataFrame(
            {
                "date": pd.date_range(start="2020-01-01", periods=5),
                "portfolio_returns": [0.01, 0.02, -0.01, 0.03, 0.02],
            }
        )
        backtest_data = BackTestSummaryAnalyticsData(data=data)
        assert isinstance(backtest_data.data.index, pd.DatetimeIndex)


class TestBackTestSummaryAnalytics:
    def test_calculate_return_metrics(self):
        """Test calculation of return metrics."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.02]
        backtest_data = create_sample_data(returns)
        analytics = BackTestSummaryAnalytics(backtest_data)

        metrics = analytics.calculate_return_metrics()
        assert "Absolute Return" in metrics
        assert "Annualized Return" in metrics
        assert "Cumulative Return" in metrics
        assert isinstance(metrics["Absolute Return"], float)

    def test_calculate_risk_adjusted_metrics(self):
        """Test calculation of risk-adjusted metrics."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.02]
        risk_free = [0.001] * len(returns)
        backtest_data = create_sample_data(returns, risk_free_rate=risk_free)
        analytics = BackTestSummaryAnalytics(backtest_data)

        metrics = analytics.calculate_risk_adjusted_metrics()
        assert "Sharpe Ratio" in metrics
        assert "Sortino Ratio" in metrics
        assert "Information Ratio" in metrics
        assert isinstance(metrics["Sharpe Ratio"], float)

    def test_calculate_risk_metrics(self):
        """Test calculation of risk metrics."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.02]
        benchmark = [0.005, 0.015, -0.005, 0.025, 0.015]
        backtest_data = create_sample_data(returns, benchmark_returns=benchmark)
        analytics = BackTestSummaryAnalytics(backtest_data)

        metrics = analytics.calculate_risk_metrics()
        assert "Volatility" in metrics
        assert "Beta" in metrics
        assert "Alpha" in metrics
        assert isinstance(metrics["Volatility"], float)

    def test_calculate_drawdown_metrics(self):
        """Test calculation of drawdown metrics."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.02]
        backtest_data = create_sample_data(returns)
        analytics = BackTestSummaryAnalytics(backtest_data)

        metrics = analytics.calculate_drawdown_metrics()
        assert "Maximum Drawdown" in metrics
        assert "Calmar Ratio" in metrics
        assert isinstance(metrics["Maximum Drawdown"], float)

    def test_summary_dataframe(self):
        """Test generation of summary dataframe."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.02]
        backtest_data = create_sample_data(returns)
        analytics = BackTestSummaryAnalytics(backtest_data)

        summary_df = analytics.summary()
        assert isinstance(summary_df, pd.DataFrame)
        assert isinstance(summary_df.index, pd.MultiIndex)
        assert "Value" in summary_df.columns

    def test_edge_case_zero_returns(self):
        """Test edge case with zero returns."""
        returns = [0.0] * 5
        backtest_data = create_sample_data(returns)
        analytics = BackTestSummaryAnalytics(backtest_data)

        metrics = analytics.calculate_all_metrics()
        assert metrics["Return Based Measures"]["Absolute Return"] == 0.0
        assert metrics["Risk Measures"]["Volatility"] == 0.0

    def test_edge_case_negative_returns(self):
        """Test edge case with all negative returns."""
        returns = [-0.01] * 5
        backtest_data = create_sample_data(returns)
        analytics = BackTestSummaryAnalytics(backtest_data)

        metrics = analytics.calculate_all_metrics()
        assert metrics["Return Based Measures"]["Absolute Return"] < 0
        assert metrics["Drawdown Metrics"]["Maximum Drawdown"] < 0
