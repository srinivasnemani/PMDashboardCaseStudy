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

    def __post_init__(self):
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


class BackTestSummaryAnalytics:
    """
    A comprehensive backtesting class that calculates various performance metrics
    for portfolio evaluation.
    """

    def __init__(self, backtest_data: BackTestSummaryAnalyticsData):
        """
        Initialize the backtesting class with backtest data.

        Parameters:
        -----------
        backtest_data : BacktestData
            Data class containing the portfolio data and parameters.
        """
        self.data = backtest_data.data
        self.trading_days_per_year = backtest_data.trading_days_per_year

        # Calculate cumulative returns
        self._calculate_cumulative_returns()

    def _calculate_cumulative_returns(self):
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
            "return_based_measures": self.calculate_return_metrics(),
            "risk_adjusted_performance": self.calculate_risk_adjusted_metrics(),
            "risk_measures": self.calculate_risk_metrics(),
            "drawdown_metrics": self.calculate_drawdown_metrics(),
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
        portfolio_returns = self.data["portfolio_returns"]
        portfolio_cumulative = self.data["portfolio_cumulative"]

        total_days = len(portfolio_returns)
        years = total_days / self.trading_days_per_year

        absolute_return = portfolio_cumulative.iloc[-1]
        annualized_return = (1 + absolute_return) ** (1 / years) - 1

        return_metrics = {
            "absolute_return": absolute_return,
            "annualized_return": annualized_return,
            "cumulative_return": absolute_return,
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

        ann_factor = np.sqrt(self.trading_days_per_year)
        portfolio_volatility = portfolio_returns.std() * ann_factor

        ann_excess_return = excess_returns.mean() * self.trading_days_per_year

        sharpe_ratio = (
            ann_excess_return / portfolio_volatility if portfolio_volatility != 0 else 0
        )

        # For varying risk-free rate, calculate downside deviations point by point
        is_downside = portfolio_returns < risk_free_rate
        downside_returns = portfolio_returns[is_downside] - risk_free_rate[is_downside]

        downside_deviation = (
            downside_returns.std() * ann_factor if len(downside_returns) > 0 else 0
        )
        sortino_ratio = (
            ann_excess_return / downside_deviation if downside_deviation != 0 else 0
        )

        benchmark_returns = self.data["benchmark_returns"]
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = active_returns.std() * ann_factor
        information_ratio = (
            (active_returns.mean() * self.trading_days_per_year) / tracking_error
            if tracking_error != 0
            else 0
        )

        risk_adjusted_metrics = {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "information_ratio": information_ratio,
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

        volatility = portfolio_returns.std() * np.sqrt(self.trading_days_per_year)

        benchmark_returns = self.data["benchmark_returns"]
        risk_free_rate = self.data["risk_free_rate"]

        covariance = (
            portfolio_returns.cov(benchmark_returns) * self.trading_days_per_year
        )
        benchmark_variance = benchmark_returns.var() * self.trading_days_per_year
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0

        # Calculate Alpha with time-varying risk-free rate
        excess_portfolio = portfolio_returns - risk_free_rate
        excess_benchmark = benchmark_returns - risk_free_rate
        alpha = excess_portfolio.mean() - beta * excess_benchmark.mean()
        alpha = alpha * self.trading_days_per_year

        risk_metrics = {"volatility": volatility, "beta": beta, "alpha": alpha}

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
        portfolio_returns = self.data["portfolio_returns"]
        years = len(portfolio_returns) / self.trading_days_per_year
        absolute_return = portfolio_cumulative.iloc[-1]
        annualized_return = (1 + absolute_return) ** (1 / years) - 1
        calmar_ratio = (
            abs(annualized_return / max_drawdown) if max_drawdown != 0 else float("inf")
        )

        drawdown_metrics = {
            "maximum_drawdown": max_drawdown,
            "calmar_ratio": calmar_ratio,
        }

        return drawdown_metrics

    def summary(self) -> pd.DataFrame:
        """
        Generate a summary dataframe with all metrics using multi-index.

        Returns:
        --------
        pd.DataFrame
            DataFrame with all metrics organized by category.
        """
        metrics = self.calculate_all_metrics()

        # Format category and metric names
        formatted_metrics = {}
        for category, metrics_dict in metrics.items():
            # Format category name: remove underscores and capitalize first letter of each word
            formatted_category = " ".join(
                word.capitalize() for word in category.split("_")
            )

            for metric_name, value in metrics_dict.items():
                # Format metric name: remove underscores and capitalize first letter of each word
                formatted_metric = " ".join(
                    word.capitalize() for word in metric_name.split("_")
                )
                formatted_metrics[(formatted_category, formatted_metric)] = value

        # Create multi-index DataFrame
        index_tuples = list(formatted_metrics.keys())
        multi_index = pd.MultiIndex.from_tuples(
            index_tuples, names=["Category", "Metric"]
        )

        summary_df = pd.DataFrame(
            {"Value": list(formatted_metrics.values())}, index=multi_index
        )

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
