from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.data_access.risk_model import RiskModelDataUtil
from src.data_access.trade_booking import get_trade_and_sec_master_data


class RiskFactorAttributions:
    """
    A class for analyzing risk factor attributions in a portfolio.

    Parameters:
    -----------
    trade_data_df : pd.DataFrame
        The trade data including ticker, shares, prices, direction, etc.
    rm_obj : RiskModel object
        Contains factor exposures, specific risk residuals, factor covariance, and factor names.
    trade_direction : str, optional
        Filter trades by direction ('Long' or 'Short'). Default is None (all trades).
    """

    def __init__(self, trade_data_df: pd.DataFrame, rm_obj: Any, trade_direction: Optional[str] = None) -> None:
        self.trade_data_df = trade_data_df
        self.rm_obj = rm_obj
        self.trade_direction = trade_direction

    def compute_factor_pnl_attribution(self) -> pd.DataFrame:
        """
        Calculate factor PnL attribution for the portfolio, adjusted for long-short trades.
        Signed factor exposures are normalized over gross exposure.
        """
        import numpy as np
        import pandas as pd
        from sklearn.linear_model import LinearRegression

        trade_data = self.trade_data_df
        risk_obj = self.rm_obj
        trade_direction = self.trade_direction

        factor_exposures = risk_obj.factor_exposures
        factors = risk_obj.factor_names

        # Step 1: Filter trades by direction if specified
        if trade_direction is not None and trade_direction.upper() == "LONG":
            trade_data_selected = trade_data[trade_data["direction"] == "Long"].copy()
        elif trade_direction is not None and trade_direction.upper() == "SHORT":
            trade_data_selected = trade_data[trade_data["direction"] == "Short"].copy()
        else:
            trade_data_selected = trade_data.copy()

        # Step 2: Compute position weights and PnL
        trade_data_selected["gross_position_weight"] = (
                trade_data_selected["shares"].abs() * trade_data_selected["trade_close_price"]
        )
        trade_data_selected["position_weight"] = trade_data_selected["gross_position_weight"]

        trade_data_selected["pnl"] = trade_data_selected["shares"] * (
                trade_data_selected["trade_close_price"] - trade_data_selected["trade_open_price"]
        )

        # Step 3: Align and merge factor exposures
        trade_data_selected = trade_data_selected.rename(columns={"trade_open_date": "date"})
        trade_data_selected["date"] = pd.to_datetime(trade_data_selected["date"])
        factor_exposures["date"] = pd.to_datetime(factor_exposures["date"])

        merged = pd.merge(
            trade_data_selected,
            factor_exposures,
            on=["date", "ticker"],
            how="left"
        )

        # Step 4: Prepare regression inputs
        X = merged[factors].fillna(0)
        y = merged["pnl"].fillna(0)

        # Step 5: Fit linear regression (no intercept)
        model = LinearRegression(fit_intercept=False)
        model.fit(X, y)
        factor_returns = pd.Series(model.coef_, index=factors)

        # Step 6: Compute factor PnL contributions
        factor_exposure_sums = X.sum()  # signed sum of exposures
        factor_pnl = factor_returns * factor_exposure_sums

        # Step 7: Compute residual PnL
        predicted_pnl = X @ factor_returns
        merged["residual_pnl"] = y - predicted_pnl
        residual_pnl_total = merged["residual_pnl"].sum()

        # Step 8: Attribution table
        attribution = pd.DataFrame({
            "factor_pnl": factor_pnl,
            "exposure": factor_exposure_sums
        })

        # Signed exposure normalized by gross exposure
        gross_exposure = attribution["exposure"].abs().sum()
        attribution["factor_exposure_pct"] = attribution["exposure"] / gross_exposure
        attribution["pnl_contribution_pct"] = attribution["factor_pnl"] / y.sum()

        # Step 9: Add residual row
        residual_row = pd.Series({
            "factor_pnl": residual_pnl_total,
            "exposure": np.nan,
            "factor_exposure_pct": np.nan,
            "pnl_contribution_pct": residual_pnl_total / y.sum(),
        }, name="Residual")

        attribution = pd.concat([attribution, residual_row.to_frame().T])

        # Final formatting
        attribution = attribution.rename(columns={"factor_pnl": "factor_pnl_usd"})
        selected_columns = ["factor_pnl_usd", "factor_exposure_pct", "pnl_contribution_pct"]
        attribution = attribution[selected_columns]
        attribution = attribution.sort_values("pnl_contribution_pct", ascending=False)

        return attribution

    def compute_portfolio_risk_decomposition(self) -> pd.DataFrame:
        """
        Decomposes portfolio risk into factor and specific risk.
        Returns both original and annualized variance and volatility metrics.

        Returns:
        --------
        pd.DataFrame
            Decomposition of portfolio risk: factor contribution and specific risk
        """

        trade_df = self.trade_data_df
        rm_obj = self.rm_obj
        trade_direction = self.trade_direction

        # Step 1: Filter by trade direction if specified
        if trade_direction is not None:
            if trade_direction.upper() == "LONG":
                trade_df = trade_df[trade_df["direction"] == "Long"].copy()
            elif trade_direction.upper() == "SHORT":
                trade_df = trade_df[trade_df["direction"] == "Short"].copy()

        # Combine factor exposures, specific risk and residuals into one data frame
        risk_df = pd.merge(
            rm_obj.factor_exposures,
            rm_obj.sp_risk_residuals,
            on=["date", "ticker"],
            how="left",
        )
        factor_cov_df = rm_obj.factor_covariance
        factor_columns = rm_obj.factor_names

        # Merge trade and risk data
        merged_df = pd.merge(trade_df, risk_df, on="ticker", how="inner")

        # Calculate signed market values (preserving short position negative signs)
        merged_df["signed_market_value"] = merged_df["shares"] * merged_df["trade_open_price"]

        # Calculate absolute market values for normalization
        merged_df["abs_market_value"] = abs(merged_df["signed_market_value"])
        total_abs_mv = merged_df["abs_market_value"].sum()

        # Calculate weights preserving signs but normalized by absolute total
        merged_df["weight"] = merged_df["signed_market_value"] / total_abs_mv

        # Construct matrix of weighted factor exposures
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_factor_exposure = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor covariance matrix
        factor_cov_matrix = factor_cov_df.loc[factor_columns, factor_columns].values

        # Factor risk (systematic) - in variance units
        factor_risk = float(
            (
                    portfolio_factor_exposure.T
                    @ factor_cov_matrix
                    @ portfolio_factor_exposure
            )[0, 0]
        )

        # Specific risk (idiosyncratic) - in variance units
        merged_df["specific_variance"] = merged_df["specific_risk"] ** 2
        specific_risk = float(
            (merged_df["weight"] ** 2 * merged_df["specific_variance"]).sum()
        )

        # Total risk - in variance units
        total_risk = factor_risk + specific_risk

        # factor model uses daily risk metrics:
        periods_per_year = 252

        # Variance scaling - multiply by number of periods
        factor_risk_annual = factor_risk * periods_per_year
        specific_risk_annual = specific_risk * periods_per_year
        total_risk_annual = total_risk * periods_per_year

        # Volatility scaling - multiply by square root of number of periods
        vol_scaling_factor = np.sqrt(periods_per_year)
        factor_volatility = np.sqrt(factor_risk)
        specific_volatility = np.sqrt(specific_risk)
        total_volatility = np.sqrt(total_risk)

        factor_volatility_annual = factor_volatility * vol_scaling_factor
        specific_volatility_annual = specific_volatility * vol_scaling_factor
        total_volatility_annual = total_volatility * vol_scaling_factor

        # Risk contributions
        risk_decomposition = pd.DataFrame(
            {

                # Annualized variance metrics
                "Factor Risk (Annualized Variance)": [factor_risk_annual],
                "Specific Risk (Annualized Variance)": [specific_risk_annual],
                "Total Risk (Annualized Variance)": [total_risk_annual],

                # Annualized volatility metrics
                "Factor Risk (Annualized Vol)": [factor_volatility_annual],
                "Specific Risk (Annualized Vol)": [specific_volatility_annual],
                "Total Risk (Annualized Vol)": [total_volatility_annual],

                # Contribution percentages (unchanged)
                "Factor Risk Contribution %": [factor_risk / total_risk],
                "Specific Risk Contribution %": [specific_risk / total_risk],

            }
        )

        return risk_decomposition

    def compute_full_risk_decomposition(self) -> pd.DataFrame:
        """
        Computes a comprehensive risk decomposition including factor and specific risk contributions.
        Properly handles long-short portfolios and ensures contribution percentages sum to 100%
        using the absolute method, which is most appropriate for long-short portfolios.

        Returns:
        --------
        pd.DataFrame
            Complete risk decomposition including factor and specific risk contributions.
        """
        import numpy as np

        trade_df = self.trade_data_df
        rm_obj = self.rm_obj
        trade_direction = self.trade_direction

        # Step 1: Filter by trade direction if specified
        if trade_direction is not None:
            if trade_direction.upper() == "LONG":
                trade_df = trade_df[trade_df["direction"] == "Long"].copy()
            elif trade_direction.upper() == "SHORT":
                trade_df = trade_df[trade_df["direction"] == "Short"].copy()

        # Combine factor exposures, specific risk and residuals into one data frame
        risk_df = pd.merge(
            rm_obj.factor_exposures,
            rm_obj.sp_risk_residuals,
            on=["date", "ticker"],
            how="left",
        )
        factor_cov_df = rm_obj.factor_covariance
        factor_columns = rm_obj.factor_names

        # Merge trade and risk data
        merged_df = pd.merge(trade_df, risk_df, on="ticker", how="inner")

        # Calculate signed market values (preserving short position negative signs)
        merged_df["signed_market_value"] = merged_df["shares"] * merged_df["trade_open_price"]

        # Calculate absolute market values for normalization
        merged_df["abs_market_value"] = abs(merged_df["signed_market_value"])
        total_abs_mv = merged_df["abs_market_value"].sum()

        # Calculate weights preserving signs but normalized by absolute total
        merged_df["weight"] = merged_df["signed_market_value"] / total_abs_mv

        # Construct matrix of weighted factor exposures
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_factor_exposure = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor covariance matrix
        factor_cov_matrix = factor_cov_df.loc[factor_columns, factor_columns].values

        # Factor risk (systematic) in variance units
        factor_risk = float(
            (
                    portfolio_factor_exposure.T
                    @ factor_cov_matrix
                    @ portfolio_factor_exposure
            )[0, 0]
        )

        # Specific risk (idiosyncratic) in variance units
        merged_df["specific_variance"] = merged_df["specific_risk"] ** 2
        specific_risk = float(
            (merged_df["weight"] ** 2 * merged_df["specific_variance"]).sum()
        )

        # Total risk in variance units
        total_risk = factor_risk + specific_risk

        # Marginal contribution to risk
        # Use safe division to avoid issues when factor_risk is very small
        safe_factor_risk = max(factor_risk, 1e-10)  # Prevent division by very small numbers
        marginal_contribution = (
                (factor_cov_matrix @ portfolio_factor_exposure).flatten()
                / np.sqrt(safe_factor_risk)
        )

        # Factor risk contribution
        factor_risk_contribution = (
                marginal_contribution * portfolio_factor_exposure.flatten()
        )

        # Create output DataFrame for factors
        risk_decomposition = pd.DataFrame(
            {
                "Factor": factor_columns,
                "Portfolio Exposure": portfolio_factor_exposure.flatten(),
                "Marginal Contribution": marginal_contribution,
                "Risk Contribution": factor_risk_contribution,
            }
        )

        # Add specific risk row
        specific_row = pd.Series(
            {
                "Factor": "Specific Risk",
                "Portfolio Exposure": np.nan,
                "Marginal Contribution": np.nan,
                "Risk Contribution": specific_risk,
            },
            name="Specific",
        )

        # Append the row to the DataFrame
        risk_decomposition = pd.concat([risk_decomposition, specific_row.to_frame().T])

        # Calculate contribution percentages using absolute values
        # This is the most appropriate method for long-short portfolios
        absolute_contributions = np.abs(risk_decomposition["Risk Contribution"])
        total_abs_contribution = absolute_contributions.sum()

        # Store the contribution percentage (will sum to 100%)
        risk_decomposition["Contribution %"] = absolute_contributions / total_abs_contribution * 100

        # Add total row
        total_row = pd.Series(
            {
                "Factor": "Total",
                "Portfolio Exposure": np.nan,
                "Marginal Contribution": np.nan,
                "Risk Contribution": total_risk,
                "Contribution %": 100.0,
            },
            name="Total",
        )
        risk_decomposition = pd.concat([risk_decomposition, total_row.to_frame().T])

        # Add net exposure ratio information as a property of the object
        self.net_exposure_ratio = merged_df["weight"].sum()

        # Return risk decomposition DataFrame
        return risk_decomposition

    def compute_all_factor_attributions(self) -> Dict[str, pd.DataFrame]:
        """
        Computes all factor attributions and returns them in a dictionary.

        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary containing all factor attributions.
        """
        pnl_attribution = self.compute_factor_pnl_attribution()
        risk_decomposition = self.compute_portfolio_risk_decomposition()
        full_risk_decomposition = self.compute_full_risk_decomposition()

        return {
            "factor_pnl_attribution": pnl_attribution,
            "portfolio_risk_decomposition": risk_decomposition,
            "full_risk_decomposition": full_risk_decomposition,
        }


def demo_run() -> None:
    """
    Demo function to run the risk factor attributions.
    """
    # Example usage
    valuation_date = "2024-11-22"
    strategy_name = "Mom_RoC"  # "MinVol"
    trade_data = get_trade_and_sec_master_data(strategy_name, valuation_date, valuation_date)
    risk_model = RiskModelDataUtil.fetch_risk_model(valuation_date)
    risk_attributions = RiskFactorAttributions(trade_data, risk_model)
    results = risk_attributions.compute_all_factor_attributions()
    print(results)


# Example usage
if __name__ == "__main__":
    demo_run()
