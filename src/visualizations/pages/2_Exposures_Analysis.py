import os

import streamlit as st

from src.visualizations.charts.ts_exposures_plots import (
    render_exposure_time_series, render_leverage_time_series)
from src.visualizations.data_preparation.exposures_anlaysis import (
    get_aum_leverage_ts, get_exposures_time_series)
from src.visualizations.ui_elements.side_bar_user_selections import \
    fetch_user_selection_strategies_and_bt_dates


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


def render_exposure_ts(exposure_ts_df):
    st.subheader("Exposures Over Time")
    tab_1, tab_2 = st.tabs(["Exposure USD", "Table"])

    with tab_1:
        plotly_fig = render_exposure_time_series(exposure_ts_df, measure_type="USD")
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        st.dataframe(exposure_ts_df, use_container_width=True)


def render_capital_and_leverage_ts(aum_leverage_df):
    st.subheader("Capital, Leverage Over Time")
    leverage_tab_1, leverage_tab_2, leverage_tab_3, leverage_tab_4 = st.tabs(
        ["Leverage", "Capital", "Target Exposure", "Table"])

    with leverage_tab_1:
        plotly_fig = render_leverage_time_series(aum_leverage_df, measure_type="Leverage")
        st.plotly_chart(plotly_fig, use_container_width=True)
    with leverage_tab_2:
        plotly_fig = render_leverage_time_series(aum_leverage_df, measure_type="Capital")
        st.plotly_chart(plotly_fig, use_container_width=True)
    with leverage_tab_3:
        plotly_fig = render_leverage_time_series(aum_leverage_df, measure_type="Target Exposure")
        st.plotly_chart(plotly_fig, use_container_width=True)
    with leverage_tab_4:
        st.dataframe(aum_leverage_df, use_container_width=True)


def render_backtest_summary():
    st.set_page_config(layout="wide")
    load_css_files()
    selected_strategy, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()

    st.subheader(f"Analysis for the strategy: {selected_strategy}")
    st.markdown(f"Date Range: `{start_date.strftime('%Y-%m-%d')}` to `{end_date.strftime('%Y-%m-%d')}`")

    exposures_ts_df = get_exposures_time_series(selected_strategy, start_date, end_date)
    render_exposure_ts(exposures_ts_df)

    aum_leverage_df = get_aum_leverage_ts(selected_strategy, start_date, end_date)
    render_capital_and_leverage_ts(aum_leverage_df)


if __name__ == "__main__":
    render_backtest_summary()
