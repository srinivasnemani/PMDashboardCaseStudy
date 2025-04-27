import os

import streamlit as st
from sqlalchemy import text

from src.analytics.trade_summary import (get_pnl_exposure_by_gics_sector,
                                         get_pnl_exposure_time_series)
from src.data_access.crud_util import DataAccessUtil
from src.data_access.trade_booking import get_trade_and_sec_master_data
from src.visualizations.charts.pnl_ts_chart_by_gics_sector import \
    plot_ts_gics_sector_pnl
from src.visualizations.charts.pnl_ts_chart_by_trade_type import \
    plot_pnl_series_by_trade_direction
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


def fetch_pnl_by_gics_groups(strategy_name, start_date, end_date):
    trade_data_df = get_trade_and_sec_master_data(strategy_name, start_date, end_date)
    result = get_pnl_exposure_by_gics_sector(trade_data_df)
    return result


def fetch_pnl_exposures_ts(strategy_name, start_date, end_date):
    sql_query = f""" SELECT * FROM trade_booking tb where 
                    tb.strategy_name  = "{strategy_name}"
                    and tb.trade_open_date >= date('{start_date}')
                    and tb.trade_open_date <= date('{end_date}') """

    query_string = text(sql_query)
    trade_data_df = DataAccessUtil.fetch_data_from_db(query_string)
    result = get_pnl_exposure_time_series(trade_data_df)
    return result


def render_pnl_ts_chart_by_trade_direction(exposure_ts_df):
    st.subheader("P&L Over Time by Trade direction")
    exposures_tab_1, exposures_tab_2 = st.tabs(["PnL Time Series", "Table"])

    with exposures_tab_1:
        plotly_fig = plot_pnl_series_by_trade_direction(exposure_ts_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with exposures_tab_2:
        st.dataframe(exposure_ts_df, use_container_width=True)


def render_pnl_time_series_gics_sectors(exposure_ts_df):
    st.subheader("P&L Over Time by GICS sectors")
    exposures_tab_1, exposures_tab_2 = st.tabs(["PnL Time Series", "Table"])

    with exposures_tab_1:
        plotly_fig = plot_ts_gics_sector_pnl(exposure_ts_df)
        st.plotly_chart(plotly_fig, use_container_width=True)
    with exposures_tab_2:
        st.dataframe(exposure_ts_df, use_container_width=True)


def render_performance_page():
    st.set_page_config(layout="wide")
    load_css_files()

    strategy_name, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()
    st.subheader(f"Analysis for the strategy: {strategy_name}")
    st.markdown(f"Date Range: `{start_date.strftime('%Y-%m-%d')}` to `{end_date.strftime('%Y-%m-%d')}`")

    pnl_group_by_trade_direction = fetch_pnl_exposures_ts(strategy_name, start_date, end_date)
    render_pnl_ts_chart_by_trade_direction(pnl_group_by_trade_direction)

    pnl_group_by_gics = fetch_pnl_by_gics_groups(strategy_name, start_date, end_date)
    render_pnl_time_series_gics_sectors(pnl_group_by_gics)


if __name__ == "__main__":
    render_performance_page()
