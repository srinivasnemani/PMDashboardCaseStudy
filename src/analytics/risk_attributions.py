import numpy as np
import pandas as pd
from src.data_access.risk_model import RiskModelDataUtil
from src.data_access.trade_booking import get_trade_and_sec_master_data
from sklearn.linear_model import LinearRegression


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

    def __init__(self, trade_data_df, rm_obj, trade_direction=None):
        self.trade_data_df = trade_data_df
        self.rm_obj = rm_obj
        self.trade_direction = trade_direction

    def compute_factor_pnl_attribution(self):
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

    def compute_portfolio_risk_decomposition(self):
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

    def compute_factor_risk_marginal_contributions(self):
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

        # Merge
        merged_df = pd.merge(trade_df, risk_df, on="ticker", how="inner")
        merged_df["market_value"] = merged_df["shares"] * merged_df["trade_open_price"]
        total_mv = merged_df["market_value"].sum()
        merged_df["weight"] = merged_df["market_value"] / total_mv

        # Weighted exposures
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_beta = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor risk decomposition
        factor_cov = factor_cov_df.loc[factor_columns, factor_columns].values
        total_factor_risk = float(
            (portfolio_beta.T @ factor_cov @ portfolio_beta)[0, 0]
        )

        # Marginal contribution
        marginal_contrib = (factor_cov @ portfolio_beta).flatten()
        risk_contrib = portfolio_beta.flatten() * marginal_contrib

        # Wrap into DataFrame
        contrib_df = pd.DataFrame(
            {
                "Factor": factor_columns,
                "Risk Contribution": risk_contrib,
                "Contribution %": risk_contrib / total_factor_risk,
            }
        )

        return contrib_df.sort_values("Contribution %", ascending=False)

    def compute_full_risk_decomposition(self):
        """
        Returns risk decomposition including per-factor contributions and specific risk,
        normalized to sum to 100% of total portfolio risk.

        Returns:
        --------
        pd.DataFrame
            DataFrame with ['Source', 'Risk Contribution', 'Contribution %']
            summing to 100% of total portfolio risk.
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

        merged_df = pd.merge(trade_df, risk_df, on="ticker", how="inner")
        merged_df["market_value"] = merged_df["shares"] * merged_df["trade_open_price"]
        total_mv = merged_df["market_value"].sum()
        merged_df["weight"] = merged_df["market_value"] / total_mv

        # Portfolio factor exposure
        exposure_matrix = merged_df[factor_columns].multiply(
            merged_df["weight"], axis=0
        )
        portfolio_beta = exposure_matrix.sum().values.reshape(-1, 1)

        # Factor risk: βᵗ Σ β
        factor_cov = factor_cov_df.loc[factor_columns, factor_columns].values
        total_factor_risk = float(
            (portfolio_beta.T @ factor_cov @ portfolio_beta)[0, 0]
        )

        # Specific risk
        merged_df["specific_variance"] = merged_df["specific_risk"] ** 2
        specific_risk = float(
            (merged_df["weight"] ** 2 * merged_df["specific_variance"]).sum()
        )

        # Total risk
        total_risk = total_factor_risk + specific_risk

        # Individual factor contributions (marginal)
        marginal_contrib = (factor_cov @ portfolio_beta).flatten()
        factor_contrib = portfolio_beta.flatten() * marginal_contrib  # Absolute

        # Scale to percentage of total portfolio risk
        factor_contrib_pct = factor_contrib / total_risk
        specific_contrib_pct = specific_risk / total_risk

        # Construct unified table
        data = {
            "Factor": list(factor_columns) + ["Specific Risk"],
            "Risk Contribution": list(factor_contrib) + [specific_risk],
            "Contribution %": list(factor_contrib_pct) + [specific_contrib_pct],
        }

        return (
            pd.DataFrame(data)
            .sort_values("Contribution %", ascending=False)
            .reset_index(drop=True)
        )

    def compute_all_factor_attributions(self):
        """
        Get attribution_results from all four methods.

        Returns:
        --------
        dict
            A dictionary containing the attribution_results of all four calculation methods.
        """
        attribution_results = {
            "factor_pnl_attribution": self.compute_factor_pnl_attribution(),
            "portfolio_risk_decomposition": self.compute_portfolio_risk_decomposition(),
            "factor_risk_marginal_contributions": self.compute_factor_risk_marginal_contributions(),
            "full_risk_decomposition": self.compute_full_risk_decomposition(),
        }
        return attribution_results


def demo_run():
    model_date = "2024-07-19"
    trade_data_df = get_trade_and_sec_master_data("MinVol", model_date, model_date)

    rm_obj = RiskModelDataUtil.fetch_risk_model(model_date)
    result_df = pd.merge(
        rm_obj.factor_exposures,
        rm_obj.sp_risk_residuals,
        on=["date", "ticker"],
        how="left",
    )

    risk_analysis = RiskFactorAttributions(trade_data_df, rm_obj)

    # Get results for all trades
    all_results = risk_analysis.compute_all_factor_attributions()
    df = all_results["full_risk_decomposition"]
    df.to_clipboard()


# Example usage
if __name__ == "__main__":
    demo_run()
