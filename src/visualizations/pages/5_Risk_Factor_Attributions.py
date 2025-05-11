import os

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from src.analytics.risk_attributions import RiskFactorAttributions
from src.data_access.risk_model import RiskModelDataUtil
from src.data_access.trade_booking import get_trade_and_sec_master_data
from src.visualizations.charts.factor_pnl_contribution_chart import \
    plot_factor_pnl_attributions
from src.visualizations.charts.factor_risk_contributions_chart import \
    plot_risk_contribution_by_factor
from src.visualizations.charts.portfolio_risk_decomposition_chart import \
    plot_portfolio_risk_decomposition
from src.visualizations.ui_elements.side_bar_user_selections import (
    select_one_bt_date, select_strategy)

# =============================================================================
# Risk Factor Attributions Dashboard
# This page provides in-depth analysis of risk factor contributions:
# - Attribution of P&L to various risk factors
# - Portfolio risk decomposition (factor vs idiosyncratic)
# - Risk contribution breakdown by individual factors
# - Interactive charts and downloadable tables for all metrics
# =============================================================================

st.set_page_config(layout="wide")
st.markdown(
    "<h2 style='text-align: center;'>Risk Factor Attributions</h2>",
    unsafe_allow_html=True,
)


def load_css_files():
    kpi_exposures = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "css_styles", "kpi_exposures_style.css"
        )
    )
    wider_layout_css = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "css_styles", "wider_layout_for_graphs.css"
        )
    )

    with open(kpi_exposures) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    with open(wider_layout_css) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def calculate_risk_model_attributions(strategy_name, date_val):
    # trade_data is fetched only for one as the attributions for single day.
    trade_data_df = get_trade_and_sec_master_data(
        strategy_name, start_date=date_val, end_date=date_val
    )
    risk_model_obj = RiskModelDataUtil.fetch_risk_model(date_val)
    risk_attributions_obj = RiskFactorAttributions(trade_data_df, risk_model_obj)
    risk_attributions = risk_attributions_obj.compute_all_factor_attributions()
    return risk_attributions


def render_pnl_attributions(pnl_attribution_df):
    st.subheader("Factor Exposures and PnL decomposition")
    tab_1, tab_2 = st.tabs(["PnL Attributions", "Table"])

    pnl_attribution_df["sector"] = pnl_attribution_df.index
    pnl_attribution_df = pnl_attribution_df.reset_index(drop=True)
    pnl_attribution_df = pnl_attribution_df[
        ["sector", "factor_pnl_usd", "factor_exposure_pct", "pnl_contribution_pct"]
    ]

    with tab_1:
        plotly_fig = plot_factor_pnl_attributions(pnl_attribution_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        csv = pnl_attribution_df.to_csv(index=False)
        st.download_button(
            "Download Table as CSV", csv, "pnl_attribution.csv", "text/csv"
        )
        gb = GridOptionsBuilder.from_dataframe(pnl_attribution_df)
        gb.configure_column("sector", type=["textColumn"])
        gb.configure_column(
            "factor_pnl_usd",
            type=["numericColumn"],
            valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
        )
        gb.configure_column(
            "factor_exposure_pct",
            type=["numericColumn"],
            valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%'",
        )
        gb.configure_column(
            "pnl_contribution_pct",
            type=["numericColumn"],
            valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%'",
        )
        gridOptions = gb.build()
        AgGrid(
            pnl_attribution_df,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_portfolio_risk_decomposition(risk_decomp_df):
    st.subheader("Risk decomposition Factors vs Idio")
    tab_1, tab_2 = st.tabs(["Risk Decomposition", "Table"])
    with tab_1:
        plotly_fig = plot_portfolio_risk_decomposition(risk_decomp_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        csv = risk_decomp_df.to_csv(index=False)
        st.download_button(
            label="Download Table as CSV",
            data=csv,
            file_name="risk_decomposition.csv",
            mime="text/csv",
        )
        gb = GridOptionsBuilder.from_dataframe(risk_decomp_df)
        for col in risk_decomp_df.columns:
            if col.endswith("(Annualized Variance)"):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toFixed(4)",
                )
            elif col.endswith("(Annualized Vol)"):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : (x * 100).toFixed(2) + ' (%)'",
                )
            elif col in ["Factor Risk Contribution %", "Specific Risk Contribution %"]:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%'",
                )
            elif col == "Net Exposure Ratio":
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toFixed(2)",
                )
            else:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toFixed(2)",
                )
        gridOptions = gb.build()
        AgGrid(
            risk_decomp_df,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_factors_contributions(factors_risk_contribution_df):
    st.subheader("Risk Contribution Breakdown by Factor")
    tab_1, tab_2 = st.tabs(["Factors Contributions", "Table"])
    with tab_1:
        plotly_fig = plot_risk_contribution_by_factor(factors_risk_contribution_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        csv = factors_risk_contribution_df.to_csv(index=False)
        st.download_button(
            label="Download Table as CSV",
            data=csv,
            file_name="factors_risk_contribution.csv",
            mime="text/csv",
        )
        gb = GridOptionsBuilder.from_dataframe(factors_risk_contribution_df)
        for col in factors_risk_contribution_df.columns:
            if col in ["factor_pnl_usd"]:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : '$' + x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
                )
            elif col == "Risk Contribution":
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
                )
            elif col.endswith("_pct") or col == "Contribution %":
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%'",
                )
            else:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toFixed(2)",
                )
        gridOptions = gb.build()
        AgGrid(
            factors_risk_contribution_df,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_risk_attribution_page():
    load_css_files()
    strategy_name = select_strategy()
    selected_date = select_one_bt_date()
    st.markdown(
        f"<h6 style='text-align: left;'>Analysis for the strategy: '{strategy_name}' and for the date: '{selected_date}'</h6>",
        unsafe_allow_html=True,
    )

    risk_attributions = calculate_risk_model_attributions(strategy_name, selected_date)
    render_pnl_attributions(risk_attributions["factor_pnl_attribution"])
    render_portfolio_risk_decomposition(
        risk_attributions["portfolio_risk_decomposition"]
    )
    render_factors_contributions(risk_attributions["full_risk_decomposition"])


if __name__ == "__main__":
    render_risk_attribution_page()
