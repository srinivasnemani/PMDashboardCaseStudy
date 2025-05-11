import math
import os

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from src.visualizations.charts.trade_summary_by_direction_plot import \
    plot_exposures_by_direction
from src.visualizations.charts.trade_summary_by_net_total import \
    plot_sector_exposure_by_total_and_net
from src.visualizations.data_preparation.trade_data_analysis import \
    get_exposures_by_direction_net_total
from src.visualizations.ui_elements.side_bar_user_selections import (
    fetch_user_selection_strategies_and_one_bt_date, select_one_bt_date,
    select_strategy)

# =============================================================================
# Rebalance Analysis Dashboard
# This page provides analysis of exposures and trade summaries at each rebalance:
# - Exposure breakdown by trade direction (long/short/net)
# - Sector exposure analysis by total and net values
# - Interactive charts and downloadable tables for all exposure metrics
# =============================================================================

st.set_page_config(layout="wide")
st.markdown(
    "<h2 style='text-align: center;'>Exposure Analysis</h2>", unsafe_allow_html=True
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


def render_risk_attribution_page():
    load_css_files()

    # strategy_name, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()
    strategy_name, selected_date = fetch_user_selection_strategies_and_one_bt_date()
    st.markdown(
        f"<h4 style='text-align: center;'>Analysis for the strategy: '{strategy_name}' and for the rebalance date: '{selected_date}'</h4>",
        unsafe_allow_html=True,
    )


def render_trade_summary_by_direction(exposures_summary_by_direction):
    st.subheader("Exposure analysis - 1.")
    tab_1, tab_2 = st.tabs(["Exposures by trade directions", "Table"])

    with tab_1:
        plotly_fig = plot_exposures_by_direction(exposures_summary_by_direction)
        st.plotly_chart(plotly_fig, use_container_width=True)

    with tab_2:
        csv = exposures_summary_by_direction.to_csv(index=False)
        st.download_button(
            "Download Table as CSV", csv, "exposures_by_direction.csv", "text/csv"
        )
        gb = GridOptionsBuilder.from_dataframe(exposures_summary_by_direction)
        for col in exposures_summary_by_direction.columns:
            if col in [
                "exposure",
                "Long",
                "Short",
                "gross_exposure_usd",
                "net_exposure_usd",
            ]:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
                )
            elif col in ["exposure_pct", "gross_exposure_pct", "net_exposure_pct"]:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toFixed(2) + '%'",
                )
            elif col.endswith("_pct"):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%'",
                )
            else:
                gb.configure_column(col, type=["textColumn"])
        gridOptions = gb.build()
        AgGrid(
            exposures_summary_by_direction,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_trade_summary_by_total_net(exposures_summary_by_direction):
    st.subheader("Exposure analysis - 2.")
    tab_1, tab_2 = st.tabs(["Exposures by trade directions", "Table"])

    with tab_1:
        plotly_fig = plot_sector_exposure_by_total_and_net(
            exposures_summary_by_direction
        )
        st.plotly_chart(plotly_fig, use_container_width=True)

    with tab_2:
        csv = exposures_summary_by_direction.to_csv(index=False)
        st.download_button(
            "Download Table as CSV", csv, "exposures_by_total_net.csv", "text/csv"
        )
        gb = GridOptionsBuilder.from_dataframe(exposures_summary_by_direction)
        for col in exposures_summary_by_direction.columns:
            if col in [
                "exposure",
                "Long",
                "Short",
                "gross_exposure_usd",
                "net_exposure_usd",
            ]:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
                )
            elif col in ["exposure_pct", "gross_exposure_pct", "net_exposure_pct"]:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toFixed(2) + '%'",
                )
            elif col.endswith("_pct"):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%'",
                )
            else:
                gb.configure_column(col, type=["textColumn"])
        gridOptions = gb.build()
        AgGrid(
            exposures_summary_by_direction,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_trade_data_analysis_page():
    load_css_files()
    strategy_name = select_strategy()
    selected_date = select_one_bt_date()
    st.markdown(
        f"<h6 style='text-align: left;'>Analysis for the strategy: '{strategy_name}' and for the date: '{selected_date}'</h6>",
        unsafe_allow_html=True,
    )

    [exposures_summary_by_direction, exposures_net_total] = (
        get_exposures_by_direction_net_total(strategy_name, selected_date)
    )
    render_trade_summary_by_direction(exposures_summary_by_direction)
    render_trade_summary_by_total_net(exposures_net_total)

    # Exclude 'Total' and 'Specific' rows from the sum
    filtered = exposures_summary_by_direction[
        ~exposures_summary_by_direction.index.isin(["Total", "Specific"])
    ]
    assert math.isclose(
        filtered["exposure_pct"].sum(), 100.0, rel_tol=1e-4, abs_tol=1e-4
    )


if __name__ == "__main__":
    render_trade_data_analysis_page()
