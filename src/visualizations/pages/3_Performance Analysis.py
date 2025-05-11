import os

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from src.visualizations.charts.pnl_ts_chart_by_gics_sector import \
    plot_ts_gics_sector_pnl
from src.visualizations.charts.pnl_ts_chart_by_trade_type import \
    plot_pnl_series_by_trade_direction
from src.visualizations.data_preparation.performance_analysis import (
    fetch_pnl_by_gics_groups, fetch_pnl_exposures_ts)
from src.visualizations.ui_elements.side_bar_user_selections import (
    select_date_range, select_strategy)


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


def render_pnl_ts_chart_by_trade_direction(exposure_ts_df):
    st.subheader("P&L Over Time by Trade direction")
    exposures_tab_1, exposures_tab_2 = st.tabs(["PnL Time Series", "Table"])

    with exposures_tab_1:
        plotly_fig = plot_pnl_series_by_trade_direction(exposure_ts_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with exposures_tab_2:
        csv = exposure_ts_df.to_csv(index=False)
        st.download_button("Download Table as CSV", csv, "pnl_time_series_by_trade_direction.csv", "text/csv")
        gb = GridOptionsBuilder.from_dataframe(exposure_ts_df)
        gb.configure_column("trade_open_date", type=["dateColumnFilter", "customDateTimeFormat"], custom_format_string='yyyy-MM-dd')
        dollar_cols = [
            col for col in exposure_ts_df.columns if any(key in col for key in ["exposure", "pnl"]) and not col.endswith("pct")
        ]
        percent_cols = [
            col for col in exposure_ts_df.columns if col.endswith("pct") or col.startswith("cumulative_")
        ]
        for col in exposure_ts_df.columns:
            if col in dollar_cols:
                gb.configure_column(col, type=["numericColumn"], valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})")
            elif col in percent_cols:
                gb.configure_column(col, type=["numericColumn"], valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%' ")
        gridOptions = gb.build()
        AgGrid(exposure_ts_df, gridOptions=gridOptions, fit_columns_on_grid_load=True, theme="compact")


def render_pnl_time_series_gics_sectors(exposure_ts_df):
    st.subheader("P&L Over Time by GICS sectors")
    exposures_tab_1, exposures_tab_2 = st.tabs(["PnL Time Series", "Table"])

    with exposures_tab_1:
        plotly_fig = plot_ts_gics_sector_pnl(exposure_ts_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with exposures_tab_2:
        csv = exposure_ts_df.to_csv(index=False)
        st.download_button("Download Table as CSV", csv, "pnl_time_series_by_gics_sector.csv", "text/csv")
        gb = GridOptionsBuilder.from_dataframe(exposure_ts_df)
        gb.configure_column("trade_open_date", type=["dateColumnFilter", "customDateTimeFormat"], custom_format_string='yyyy-MM-dd')
        dollar_cols = [
            col for col in exposure_ts_df.columns if any(key in col for key in ["exposure", "pnl"]) and not col.endswith("pct")
        ]
        percent_cols = [
            col for col in exposure_ts_df.columns if col.endswith("pct") or col.startswith("cumulative_")
        ]
        for col in exposure_ts_df.columns:
            if col in dollar_cols:
                gb.configure_column(col, type=["numericColumn"], valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})")
            elif col in percent_cols:
                gb.configure_column(col, type=["numericColumn"], valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%' ")
        gridOptions = gb.build()
        AgGrid(exposure_ts_df, gridOptions=gridOptions, fit_columns_on_grid_load=True, theme="compact")


def render_performance_page():
    st.set_page_config(layout="wide")
    load_css_files()
    strategy_name = select_strategy()
    start_date, end_date = select_date_range()
    st.subheader(f"Analysis for the strategy: {strategy_name}")
    st.markdown(f"Date Range: `{start_date.strftime('%Y-%m-%d')}` to `{end_date.strftime('%Y-%m-%d')}`")

    pnl_group_by_trade_direction = fetch_pnl_exposures_ts(strategy_name, start_date, end_date)
    render_pnl_ts_chart_by_trade_direction(pnl_group_by_trade_direction)

    pnl_group_by_gics = fetch_pnl_by_gics_groups(strategy_name, start_date, end_date)
    render_pnl_time_series_gics_sectors(pnl_group_by_gics)


if __name__ == "__main__":
    render_performance_page()
