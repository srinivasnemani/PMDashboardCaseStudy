import os

import streamlit as st

from src.analytics.risk_attributions import RiskFactorAttributions
from src.data_access.risk_model import RiskModelDataUtil
from src.data_access.trade_booking import get_trade_and_sec_master_data
from src.visualizations.charts.factor_pnl_contribution_chart import \
    plot_factor_pnl_attributions
from src.visualizations.charts.factor_risk_contributions_chart import \
    plot_risk_contribution_by_factor
from src.visualizations.charts.factor_risk_marginal_contributions_plot import \
    plot_factor_marginal_risk_contributions
from src.visualizations.charts.portfolio_risk_decomposition_chart import \
    plot_portfolio_risk_decomposition
from src.visualizations.ui_elements.side_bar_user_selections import \
    fetch_user_selection_strategies_and_one_bt_date

st.set_page_config(layout="wide")


def load_css_files():
    kpi_exposures = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'css_styles', 'kpi_exposures_style.css')
    )
    wider_layout_css = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'css_styles', 'wider_layout_for_graphs.css')
    )

    with open(kpi_exposures) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    with open(wider_layout_css) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def calculate_risk_model_attributions(strategy_name, date_val):
    # trade_data is fetched only for one as the attributions for single day.
    trade_data_df = get_trade_and_sec_master_data(strategy_name, start_date=date_val, end_date=date_val)
    risk_model_obj = RiskModelDataUtil.fetch_risk_model(date_val)
    risk_attributions_obj = RiskFactorAttributions(trade_data_df, risk_model_obj)
    risk_attributions = risk_attributions_obj.compute_all_factor_attributions()
    return risk_attributions


def render_pnl_attributions(pnl_attribution_df):
    st.subheader("Factor Exposures and PnL decomposition")
    tab_1, tab_2 = st.tabs(["PnL Attributions", "Table"])

    pnl_attribution_df['sector'] = pnl_attribution_df.index
    pnl_attribution_df = pnl_attribution_df.reset_index(drop=True)
    pnl_attribution_df = pnl_attribution_df[['sector', 'factor_pnl_usd', 'factor_exposure_pct', 'pnl_contribution_pct']]

    with tab_1:
        plotly_fig = plot_factor_pnl_attributions(pnl_attribution_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
        # pass
    with tab_2:
        st.dataframe(pnl_attribution_df, use_container_width=True)


def render_portfolio_risk_decomposition(risk_decomp_df):
    st.subheader("Risk decomposition Factors vs Idio")
    tab_1, tab_2 = st.tabs(["Risk Decomposition", "Table"])
    with tab_1:
        plotly_fig = plot_portfolio_risk_decomposition(risk_decomp_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        st.dataframe(risk_decomp_df, use_container_width=True)


def render_factors_marginal_contributions(factors_marginal_contribution_df):
    st.subheader("Factors Marginal Contributions")
    tab_1, tab_2 = st.tabs(["Factors Marginal Contributions", "Table"])
    with tab_1:
        plotly_fig = plot_factor_marginal_risk_contributions(factors_marginal_contribution_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        st.dataframe(factors_marginal_contribution_df, use_container_width=True)


def render_factors_contributions(factors_risk_contribution_df):
    st.subheader("Factors Contributions to the Risk")
    tab_1, tab_2 = st.tabs(["Factors Contributions", "Table"])
    with tab_1:
        plotly_fig = plot_risk_contribution_by_factor(factors_risk_contribution_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        st.dataframe(factors_risk_contribution_df, use_container_width=True)


def render_risk_attribution_page():
    load_css_files()

    # strategy_name, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()
    strategy_name, selected_date = fetch_user_selection_strategies_and_one_bt_date()
    st.subheader(f"Analysis for the strategy: {strategy_name} and for the date: {selected_date}")

    risk_attributions = calculate_risk_model_attributions(strategy_name, selected_date)
    render_pnl_attributions(risk_attributions['factor_pnl_attribution'])
    render_portfolio_risk_decomposition(risk_attributions['portfolio_risk_decomposition'])
    render_factors_contributions(risk_attributions['full_risk_decomposition'])
    render_factors_marginal_contributions(risk_attributions['factor_risk_marginal_contributions'])


if __name__ == "__main__":
    render_risk_attribution_page()
