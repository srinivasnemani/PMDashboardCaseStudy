from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

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
        Calculate factor PnL attribution for the portfolio.

        Returns:
        --------
        pd.DataFrame
            Attribution of PnL to factors and residual.
        """
        trade_data = self.trade_data_df
        risk_obj = self.rm_obj
        trade_direction = self.trade_direction

        factor_exposures = risk_obj.factor_exposures
        factors = risk_obj.factor_names

        # Step 1: Filter only 'Long' trades
        if trade_direction is not None and trade_direction.upper() == "LONG":
            trade_data_selected = trade_data[trade_data["direction"] == "Long"].copy()
        elif trade_direction is not None and trade_direction.upper() == "SHORT":
            trade_data_selected = trade_data[trade_data["direction"] == "Short"].copy()
        else:
            trade_data_selected = trade_data.copy()

        # Step 2: Compute position weight and PnL
        trade_data_selected["position_weight"] = (
                trade_data_selected["shares"] * trade_data_selected["trade_close_price"]
        )
        trade_data_selected["pnl"] = trade_data_selected["shares"] * (
                trade_data_selected["trade_close_price"]
                - trade_data_selected["trade_open_price"]
        )

        # Step 3: Align and merge risk exposures (assuming risk is dated at trade_open_date)
        trade_data_selected = trade_data_selected.rename(
            columns={"trade_open_date": "date"}
        )

        trade_data_selected["date"] = pd.to_datetime(trade_data_selected["date"])
        factor_exposures["date"] = pd.to_datetime(factor_exposures["date"])
        merged = pd.merge(
            trade_data_selected, factor_exposures, on=["date", "ticker"], how="left"
        )

        # Step 4: Prepare regression inputs
        X = merged[factors].fillna(0)
        y = merged["pnl"].fillna(0)

        # Step 5: Fit linear regression (no intercept)
        model = LinearRegression(fit_intercept=False)
        model.fit(X, y)
        factor_returns = pd.Series(model.coef_, index=factors)

        # Step 6: Compute factor PnL contributions
        factor_exposures = X.sum()
        factor_pnl = factor_returns * factor_exposures

        # Step 7: Compute residual/idiosyncratic PnL
        predicted_pnl = X @ factor_returns
        merged["residual_pnl"] = y - predicted_pnl
        residual_pnl_total = merged["residual_pnl"].sum()

        # Step 8: Construct attribution table
        attribution = pd.DataFrame(
            {"factor_pnl": factor_pnl, "exposure": factor_exposures}
        )
        attribution["weight_pct"] = (
                attribution["exposure"] / merged["position_weight"].sum()
        )
        attribution["pnl_contribution_pct"] = attribution["factor_pnl"] / y.sum()

        # Add residual row,  First create your attribution table with all the factor rows
        attribution = pd.DataFrame(
            {"factor_pnl": factor_pnl, "exposure": factor_exposures}
        )
        attribution["weight_pct"] = (
                attribution["exposure"] / merged["position_weight"].sum()
        )
        attribution["pnl_contribution_pct"] = attribution["factor_pnl"] / y.sum()

        # Then add the residual row separately
        residual_row = pd.Series(
            {
                "factor_pnl": residual_pnl_total,
                "exposure": np.nan,
                "weight_pct": np.nan,
                "pnl_contribution_pct": residual_pnl_total / y.sum(),
            },
            name="Residual",
        )

        # Append the row to the DataFrame
        attribution = pd.concat([attribution, residual_row.to_frame().T])

        # return output
        attribution = attribution.sort_values("pnl_contribution_pct", ascending=False)

        # Rename columns and return the dataframe.
        attribution = attribution.rename(
            columns={
                "weight_pct": "factor_exposure_pct",
                "factor_pnl": "factor_pnl_usd",
            }
        )
        selected_columns = [
            "factor_pnl_usd",
            "factor_exposure_pct",
            "pnl_contribution_pct",
        ]
        attribution = attribution[selected_columns]

        return attribution

    def compute_portfolio_risk_decomposition(self) -> pd.DataFrame:
        """
        Decomposes portfolio risk into factor and specific risk.

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

        # Combine factor exposures, specific risk and residuals into one data frame for easier manipulations in calculations.
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

        # Calculate market value = shares × price
        merged_df["market_value"] = merged_df["shares"] * merged_df["trade_open_price"]

        # Normalize to get portfolio weights
        total_mv = merged_df["market_value"].sum()
        merged_df["weight"] = merged_df["market_value"] / total_mv

        # Construct matrix of weighted factor exposures
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_factor_exposure = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor covariance matrix
        factor_cov_matrix = factor_cov_df.loc[factor_columns, factor_columns].values

        # Factor risk (systematic)
        factor_risk = float(
            (
                    portfolio_factor_exposure.T
                    @ factor_cov_matrix
                    @ portfolio_factor_exposure
            )[0, 0]
        )

        # Specific risk (idiosyncratic)
        merged_df["specific_variance"] = merged_df["specific_risk"] ** 2
        specific_risk = float(
            (merged_df["weight"] ** 2 * merged_df["specific_variance"]).sum()
        )

        # Total risk
        total_risk = factor_risk + specific_risk

        # Risk contributions
        risk_decomposition = pd.DataFrame(
            {
                "Factor Risk": [factor_risk],
                "Specific Risk": [specific_risk],
                "Total Risk": [total_risk],
                "Factor %": [factor_risk / total_risk],
                "Specific %": [specific_risk / total_risk],
            }
        )

        return risk_decomposition

    def compute_factor_risk_marginal_contributions(self) -> pd.DataFrame:
        """
        Computes per-factor contribution to total factor risk.

        Returns:
        --------
        pd.DataFrame
            Factor risk contributions and their percentage of total factor risk.
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

        # Combine factor exposures, specific risk and residuals into one data frame for easier manipulations in calculations.
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

        # Calculate market value = shares × price
        merged_df["market_value"] = merged_df["shares"] * merged_df["trade_open_price"]

        # Normalize to get portfolio weights
        total_mv = merged_df["market_value"].sum()
        merged_df["weight"] = merged_df["market_value"] / total_mv

        # Construct matrix of weighted factor exposures
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_factor_exposure = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor covariance matrix
        factor_cov_matrix = factor_cov_df.loc[factor_columns, factor_columns].values

        # Factor risk (systematic)
        factor_risk = float(
            (
                    portfolio_factor_exposure.T
                    @ factor_cov_matrix
                    @ portfolio_factor_exposure
            )[0, 0]
        )

        # Marginal contribution to risk
        marginal_contribution = (
                factor_cov_matrix @ portfolio_factor_exposure
        ).flatten() / np.sqrt(factor_risk)

        # Factor risk contribution
        factor_risk_contribution = (
                marginal_contribution * portfolio_factor_exposure.flatten()
        )

        # Normalize contributions to sum to 1
        contribution_pct = factor_risk_contribution / factor_risk_contribution.sum()

        # Create output DataFrame
        risk_contributions = pd.DataFrame(
            {
                "Factor": factor_columns,
                "Marginal Contribution": marginal_contribution,
                "Risk Contribution": factor_risk_contribution,
                "Contribution %": contribution_pct,
            }
        )

        return risk_contributions

    def compute_full_risk_decomposition(self) -> pd.DataFrame:
        """
        Computes a comprehensive risk decomposition including factor and specific risk contributions.

        Returns:
        --------
        pd.DataFrame
            Complete risk decomposition including factor and specific risk contributions.
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

        # Combine factor exposures, specific risk and residuals into one data frame for easier manipulations in calculations.
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

        # Calculate market value = shares × price
        merged_df["market_value"] = merged_df["shares"] * merged_df["trade_open_price"]

        # Normalize to get portfolio weights
        total_mv = merged_df["market_value"].sum()
        merged_df["weight"] = merged_df["market_value"] / total_mv

        # Construct matrix of weighted factor exposures
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_factor_exposure = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor covariance matrix
        factor_cov_matrix = factor_cov_df.loc[factor_columns, factor_columns].values

        # Factor risk (systematic)
        factor_risk = float(
            (
                    portfolio_factor_exposure.T
                    @ factor_cov_matrix
                    @ portfolio_factor_exposure
            )[0, 0]
        )

        # Specific risk (idiosyncratic)
        merged_df["specific_variance"] = merged_df["specific_risk"] ** 2
        specific_risk = float(
            (merged_df["weight"] ** 2 * merged_df["specific_variance"]).sum()
        )

        # Total risk
        total_risk = factor_risk + specific_risk

        # Marginal contribution to risk
        marginal_contribution = (
                factor_cov_matrix @ portfolio_factor_exposure
        ).flatten() / np.sqrt(factor_risk)

        # Factor risk contribution
        factor_risk_contribution = (
                marginal_contribution * portfolio_factor_exposure.flatten()
        )

        # Create output DataFrame for factors
        risk_decomposition = pd.DataFrame(
            {
                "Factor": factor_columns,
                "Marginal Contribution": marginal_contribution,
                "Risk Contribution": factor_risk_contribution,
                "Contribution %": factor_risk_contribution / total_risk,
            }
        )

        # Add specific risk row
        specific_row = pd.Series(
            {
                "Factor": "Specific Risk",
                "Marginal Contribution": np.nan,
                "Risk Contribution": specific_risk,
                "Contribution %": specific_risk / total_risk,
            },
            name="Specific",
        )

        # Append the row to the DataFrame
        risk_decomposition = pd.concat([risk_decomposition, specific_row.to_frame().T])

        # Normalize contribution percentages to sum to 1
        risk_decomposition["Contribution %"] = risk_decomposition["Risk Contribution"] / risk_decomposition["Risk Contribution"].sum()

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
        factor_risk_contributions = self.compute_factor_risk_marginal_contributions()
        full_risk_decomposition = self.compute_full_risk_decomposition()

        return {
            "factor_pnl_attribution": pnl_attribution,
            "portfolio_risk_decomposition": risk_decomposition,
            "factor_risk_marginal_contributions": factor_risk_contributions,
            "full_risk_decomposition": full_risk_decomposition,
        }


def demo_run() -> None:
    """
    Demo function to run the risk factor attributions.
    """
    # Example usage
    trade_data = get_trade_and_sec_master_data("MinVol", "2024-01-01", "2024-12-31")
    risk_model = RiskModelDataUtil()
    risk_attributions = RiskFactorAttributions(trade_data, risk_model)
    results = risk_attributions.compute_all_factor_attributions()
    print(results)


# Example usage
if __name__ == "__main__":
    demo_run()
