from dataclasses import dataclass
from typing import Any, Dict

import numpy as np
import pandas as pd


@dataclass
class BackTestSummaryAnalyticsData:
    """
    Data class for backtesting inputs.

    Attributes:
    -----------
    data : pd.DataFrame
        DataFrame with columns: 'date', 'portfolio_returns', 'benchmark_returns', and 'risk_free_rate'.
    trading_days_per_year : int
        Number of trading days per year. Default is 252.
    """

    data: pd.DataFrame
    trading_days_per_year: int = 252

    def __post_init__(self) -> None:
        """Validate and prepare data after initialization."""

        self.data = self.data.copy()
        required_columns = ["portfolio_returns"]
        for col in required_columns:
            if col not in self.data.columns:
                raise ValueError(f"DataFrame must contain '{col}' column")

        # Ensure date is the index and is in datetime format
        if "date" in self.data.columns:
            self.data["date"] = pd.to_datetime(self.data["date"])
            self.data.set_index("date", inplace=True)

        # Ensure risk_free_rate is present, or add a default zero column
        if "risk_free_rate" not in self.data.columns:
            self.data["risk_free_rate"] = 0.0

        # Ensure benchmark_returns is present, or add a default zero column
        if "benchmark_returns" not in self.data.columns:
            self.data["benchmark_returns"] = 0.0

        # Calculate data frequency
        self.frequency = self._detect_frequency()
        self.annualization_factor = self._calculate_annualization_factor()

    def _detect_frequency(self) -> str:
        """
        Detect the frequency of the data based on the time index.

        Returns:
        --------
        str
            Frequency of the data ('D' for daily, 'W' for weekly, etc.)
        """
        if len(self.data) < 2:
            return "D"  # Default to daily if not enough data points

        time_diff = self.data.index[1] - self.data.index[0]
        days = time_diff.days

        if days == 1:
            return "D"  # Daily
        elif days == 7:
            return "W"  # Weekly
        elif days == 30 or days == 31:
            return "M"  # Monthly
        elif days == 90 or days == 91:
            return "Q"  # Quarterly
        elif days == 365 or days == 366:
            return "Y"  # Yearly
        else:
            return "D"  # Default to daily if frequency cannot be determined

    def _calculate_annualization_factor(self) -> float:
        """
        Calculate the appropriate annualization factor based on data frequency.

        Returns:
        --------
        float
            Annualization factor for the given frequency
        """
        frequency_factors = {
            "D": np.sqrt(252),  # Daily
            "W": np.sqrt(52),  # Weekly
            "M": np.sqrt(12),  # Monthly
            "Q": np.sqrt(4),  # Quarterly
            "Y": 1.0,  # Yearly
        }
        return frequency_factors.get(
            self.frequency, np.sqrt(252)
        )  # Default to daily if unknown


class BackTestSummaryAnalytics:
    """
    A comprehensive backtesting class that calculates various performance metrics
    for portfolio evaluation.
    """

    def __init__(self, backtest_data: "BackTestSummaryAnalyticsData") -> None:
        """
        Initialize the backtesting class with backtest data.

        Parameters:
        -----------
        backtest_data : BacktestData
            Data class containing the portfolio data and parameters.
        """
        self.data = backtest_data.data
        self.trading_days_per_year = backtest_data.trading_days_per_year
        self.annualization_factor = backtest_data.annualization_factor

        # Calculate cumulative returns
        self._calculate_cumulative_returns()

    def _calculate_cumulative_returns(self) -> None:
        """Calculate cumulative returns for portfolio and benchmark."""
        self.data["portfolio_cumulative"] = (
            1 + self.data["portfolio_returns"]
        ).cumprod() - 1
        self.data["benchmark_cumulative"] = (
            1 + self.data["benchmark_returns"]
        ).cumprod() - 1

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all available metrics and return as a dictionary.

        Returns:
        --------
        Dict[str, Any]
            Dictionary with all metrics organized by category.
        """
        metrics = {
            "Return Based Measures": self.calculate_return_metrics(),
            "Risk Adjusted Performance": self.calculate_risk_adjusted_metrics(),
            "Risk Measures": self.calculate_risk_metrics(),
            "Drawdown Metrics": self.calculate_drawdown_metrics(),
        }

        return metrics

    def calculate_return_metrics(self) -> Dict[str, float]:
        """
        Calculate basic return-based metrics.

        Returns:
        --------
        Dict[str, float]
            Dictionary with return-based metrics.
        """

        portfolio_cumulative = self.data["portfolio_cumulative"]
        years = (self.data.index.max() - self.data.index.min()).days / 365

        absolute_return = portfolio_cumulative.iloc[-1]
        annualized_return = (1 + absolute_return) ** (1 / years) - 1

        return_metrics = {
            "Absolute Return": absolute_return,
            "Annualized Return": annualized_return,
            "Cumulative Return": absolute_return,
        }

        return return_metrics

    def calculate_risk_adjusted_metrics(self) -> Dict[str, float]:
        """
        Calculate risk-adjusted performance metrics.

        Returns:
        --------
        Dict[str, float]
            Dictionary with risk-adjusted performance metrics.
        """
        portfolio_returns = self.data["portfolio_returns"]
        risk_free_rate = self.data["risk_free_rate"]

        excess_returns = portfolio_returns - risk_free_rate

        portfolio_volatility = portfolio_returns.std() * self.annualization_factor

        ann_excess_return = excess_returns.mean() * self.annualization_factor

        sharpe_ratio = (
            ann_excess_return / portfolio_volatility if portfolio_volatility != 0 else 0
        )

        # For varying risk-free rate, calculate downside deviations point by point
        is_downside = portfolio_returns < risk_free_rate
        downside_returns = portfolio_returns[is_downside] - risk_free_rate[is_downside]

        downside_deviation = (
            downside_returns.std() * self.annualization_factor
            if len(downside_returns) > 0
            else 0
        )
        sortino_ratio = (
            ann_excess_return / downside_deviation if downside_deviation != 0 else 0
        )

        benchmark_returns = self.data["benchmark_returns"]
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = active_returns.std() * self.annualization_factor
        information_ratio = (
            (active_returns.mean() * self.annualization_factor) / tracking_error
            if tracking_error != 0
            else 0
        )

        risk_adjusted_metrics = {
            "Sharpe Ratio": sharpe_ratio,
            "Sortino Ratio": sortino_ratio,
            "Information Ratio": information_ratio,
        }

        return risk_adjusted_metrics

    def calculate_risk_metrics(self) -> Dict[str, float]:
        """
        Calculate risk metrics.

        Returns:
        --------
        Dict[str, float]
            Dictionary with risk metrics.
        """
        portfolio_returns = self.data["portfolio_returns"]

        volatility = portfolio_returns.std() * self.annualization_factor

        benchmark_returns = self.data["benchmark_returns"]
        risk_free_rate = self.data["risk_free_rate"]

        covariance = (
            portfolio_returns.cov(benchmark_returns) * self.annualization_factor
        )
        benchmark_variance = benchmark_returns.var() * self.annualization_factor
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0

        # Calculate Alpha with time-varying risk-free rate
        excess_portfolio = portfolio_returns - risk_free_rate
        excess_benchmark = benchmark_returns - risk_free_rate
        alpha = excess_portfolio.mean() - beta * excess_benchmark.mean()
        alpha = alpha * self.annualization_factor

        # Calculate tracking error
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = active_returns.std() * self.annualization_factor

        risk_metrics = {
            "Volatility": volatility,
            "Beta": beta,
            "Alpha": alpha,
            "Tracking Error": tracking_error,
        }

        return risk_metrics

    def calculate_drawdown_metrics(self) -> Dict[str, float]:
        """
        Calculate drawdown metrics including maximum drawdown and Calmar ratio.

        Returns:
        --------
        Dict[str, float]
            Dictionary with drawdown metrics.
        """
        portfolio_cumulative = self.data["portfolio_cumulative"]
        running_max = portfolio_cumulative.cummax()
        drawdown = (portfolio_cumulative - running_max) / (1 + running_max)

        max_drawdown = drawdown.min()

        # Calculate Calmar ratio: annualized return divided by maximum drawdown
        years = (self.data.index.max() - self.data.index.min()).days / 365
        absolute_return = portfolio_cumulative.iloc[-1]
        annualized_return = (1 + absolute_return) ** (1 / years) - 1
        calmar_ratio = (
            abs(annualized_return / max_drawdown) if max_drawdown != 0 else float("inf")
        )

        drawdown_metrics = {
            "Maximum Drawdown": max_drawdown,
            "Calmar Ratio": calmar_ratio,
        }

        return drawdown_metrics

    def calculate_tracking_error(self) -> float:
        """
        Calculate the tracking error of the portfolio relative to its benchmark.
        Tracking error is the standard deviation of the difference between portfolio returns
        and benchmark returns, annualized.

        Returns:
        --------
        float
            Annualized tracking error of the portfolio.
        """
        portfolio_returns = self.data["portfolio_returns"]
        benchmark_returns = self.data["benchmark_returns"]

        # Calculate active returns (portfolio - benchmark)
        active_returns = portfolio_returns - benchmark_returns

        # Calculate tracking error (standard deviation of active returns, annualized)
        tracking_error = active_returns.std() * np.sqrt(self.trading_days_per_year)

        return tracking_error

    def summary(self) -> pd.DataFrame:
        """
        Generate a summary dataframe with all metrics using multi-index.

        Returns:
        --------
        pd.DataFrame
            DataFrame with all metrics organized by category.
        """
        metrics = self.calculate_all_metrics()

        # Create a list to store tuples for MultiIndex
        index_tuples = []
        values = []

        # Format category and metric names
        for category, metrics_dict in metrics.items():

            # Add each metric to the index tuples and values list
            for metric, value in metrics_dict.items():
                index_tuples.append((category, metric))
                values.append(value)

        # Create MultiIndex
        multi_index = pd.MultiIndex.from_tuples(
            index_tuples, names=["Category", "Metric"]
        )

        # Create DataFrame with MultiIndex
        summary_df = pd.DataFrame(values, index=multi_index, columns=["Value"])

        return summary_df


# Example usage
if __name__ == "__main__":
    # Sample data
    dates = pd.date_range(start="2020-01-01", end="2020-12-31")

    # Create sample data
    data = pd.DataFrame(
        {
            "date": dates,
            "portfolio_returns": np.random.normal(0.0005, 0.01, len(dates)),
            "benchmark_returns": np.random.normal(0.0003, 0.012, len(dates)),
            "risk_free_rate": np.full(len(dates), 0.02 / 252),  # Daily risk-free rate
        }
    )

    # Create BacktestData object
    backtest_data = BackTestSummaryAnalyticsData(data=data)

    # Create backtesting object
    backtest = BackTestSummaryAnalytics(backtest_data=backtest_data)

    # Calculate all metrics
    all_metrics = backtest.calculate_all_metrics()
    print(all_metrics)

    # Get summary dataframe
    summary = backtest.summary()
    print(summary)

    # Get underlying dataframe
    original_data = backtest.data.reset_index()
    print(original_data.head())
