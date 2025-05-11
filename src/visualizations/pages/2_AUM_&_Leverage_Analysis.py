import os

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from src.visualizations.charts.ts_exposures_plots import (
    render_exposure_time_series, render_leverage_time_series)
from src.visualizations.data_preparation.exposures_anlaysis import (
    get_aum_leverage_ts, get_exposures_time_series)
from src.visualizations.ui_elements.side_bar_user_selections import (
    select_date_range, select_strategy)

# =============================================================================
# Exposure Analysis Dashboard
# This page provides detailed analysis of portfolio exposures and leverage:
# - Time series visualization of long and short exposures
# - Capital and leverage tracking over time
# - Target exposure monitoring
# - Interactive tables with downloadable data for all metrics
# =============================================================================

st.set_page_config(layout="wide")
st.markdown(
    "<h2 style='text-align: center;'>AUM & Leverage Analysis</h2>", unsafe_allow_html=True
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


def render_exposure_ts(exposure_ts_df):
    st.subheader("Exposures Over Time")
    tab_1, tab_2 = st.tabs(["Exposure USD", "Table"])

    with tab_1:
        plotly_fig = render_exposure_time_series(exposure_ts_df, measure_type="USD")
        st.plotly_chart(plotly_fig, use_container_width=True)
    with tab_2:
        csv = exposure_ts_df.to_csv(index=False)
        st.download_button(
            "Download Table as CSV", csv, "exposures_time_series.csv", "text/csv"
        )
        gb = GridOptionsBuilder.from_dataframe(exposure_ts_df)
        # Apply formatting as specified
        gb.configure_column(
            "trade_open_date",
            type=["dateColumnFilter", "customDateTimeFormat"],
            custom_format_string="yyyy-MM-dd",
        )
        dollar_cols = [
            "long_exposure",
            "short_exposure",
            "long_pnl",
            "short_pnl",
            "total_exposure",
            "net_exposure",
            "total_pnl",
            "cumulative_long_pnl",
            "cumulative_short_pnl",
            "cumulative_total_pnl",
        ]
        percent_cols = [
            "long_pnl_pct",
            "short_pnl_pct",
            "net_pnl_pct",
            "cumulative_long_pnl_pct",
            "cumulative_short_pnl_pct",
            "cumulative_total_pnl_pct",
        ]
        for col in exposure_ts_df.columns:
            if col in dollar_cols:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
                )
            elif col in percent_cols:
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    valueFormatter="x == null ? '' : (x * 100).toFixed(2) + '%' ",
                )
        gridOptions = gb.build()
        AgGrid(
            exposure_ts_df,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_capital_and_leverage_ts(aum_leverage_df):
    st.subheader("Capital, Leverage Over Time")
    leverage_tab_1, leverage_tab_2, leverage_tab_3, leverage_tab_4 = st.tabs(
        ["Leverage", "Capital", "Target Exposure", "Table"]
    )

    with leverage_tab_1:
        plotly_fig = render_leverage_time_series(
            aum_leverage_df, measure_type="Leverage"
        )
        st.plotly_chart(plotly_fig, use_container_width=True)
    with leverage_tab_2:
        plotly_fig = render_leverage_time_series(
            aum_leverage_df, measure_type="Capital"
        )
        st.plotly_chart(plotly_fig, use_container_width=True)
    with leverage_tab_3:
        plotly_fig = render_leverage_time_series(
            aum_leverage_df, measure_type="Target Exposure"
        )
        st.plotly_chart(plotly_fig, use_container_width=True)
    with leverage_tab_4:
        csv = aum_leverage_df.to_csv(index=False)
        st.download_button("Download Table as CSV", csv, "aum_leverage.csv", "text/csv")
        gb = GridOptionsBuilder.from_dataframe(aum_leverage_df)
        # Apply formatting for aum, calculated_target_exposure, and target_leverage
        if "aum" in aum_leverage_df.columns:
            gb.configure_column(
                "aum",
                type=["numericColumn"],
                valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
            )
        if "calculated_target_exposure" in aum_leverage_df.columns:
            gb.configure_column(
                "calculated_target_exposure",
                type=["numericColumn"],
                valueFormatter="x == null ? '' : x.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})",
            )
        if "target_leverage" in aum_leverage_df.columns:
            gb.configure_column(
                "target_leverage",
                type=["numericColumn"],
                valueFormatter="x == null ? '' : x.toFixed(2)",
            )
        gridOptions = gb.build()
        AgGrid(
            aum_leverage_df,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            theme="compact",
        )


def render_backtest_summary():
    load_css_files()
    selected_strategy = select_strategy()
    start_date, end_date = select_date_range()

    st.markdown(
        f"<h6 style='text-align: left;'>Analysis for the strategy: {selected_strategy}</h6>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Date Range: `{start_date.strftime('%Y-%m-%d')}` to `{end_date.strftime('%Y-%m-%d')}`"
    )

    exposures_ts_df = get_exposures_time_series(selected_strategy, start_date, end_date)
    render_exposure_ts(exposures_ts_df)

    aum_leverage_df = get_aum_leverage_ts(selected_strategy, start_date, end_date)
    render_capital_and_leverage_ts(aum_leverage_df)


if __name__ == "__main__":
    render_backtest_summary()
