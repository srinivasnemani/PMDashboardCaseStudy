import os
import sys

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(layout="wide")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.visualizations.data_preparation.backtest_summary import \
    create_back_test_summary
from src.visualizations.ui_elements.side_bar_user_selections import \
    fetch_user_selection_strategies_and_bt_dates

# =============================================================================
# Back Test Summary Dashboard
# This page provides a comprehensive overview of backtest results, including:
# - Aggregated performance metrics across all trades
# - Long-only trade performance analysis
# - Short-only trade performance analysis
# Metrics include returns, risk measures, and various performance ratios
# =============================================================================

st.markdown(
    "<h2 style='text-align: center;'>Back Test Summary</h2>", unsafe_allow_html=True
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


def display_trade_summary(trades_summary, title):
    st.subheader(title)

    # Add light green border to AG Grid
    st.markdown(
        """
        <style>
        .ag-root {
            border: 2px solid #90ee90 !important;
            border-radius: 8px;
            box-sizing: border-box;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Convert the multi-index DataFrame to a format suitable for AG Grid
    trades_summary = trades_summary.reset_index()

    # Format Value column for return-based measures
    percentage_based_measures = [
        "Absolute Return",
        "Annualized Return",
        "Cumulative Return",
        "Volatility",
        "Maximum Drawdown",
        "Tracking Error",  # Added as it's annualized and typically shown as percentage
    ]
    decimal_based_measures = [
        "Sharpe Ratio",
        "Sortino Ratio",
        "Information Ratio",
        "Calmar Ratio",
        "Beta",
        "Alpha",
    ]
    if "Metric" in trades_summary.columns and "Value" in trades_summary.columns:
        trades_summary["Value"] = trades_summary.apply(
            lambda row: (
                f"{row['Value'] * 100:.2f}%"
                if row["Metric"] in percentage_based_measures
                and pd.notnull(row["Value"])
                else (
                    f"{row['Value']:,.2f}"
                    if row["Metric"] in decimal_based_measures
                    and pd.notnull(row["Value"])
                    else row["Value"]
                )
            ),
            axis=1,
        )

    # Download button for the table
    csv = trades_summary.to_csv(index=False)
    st.download_button(
        "Download Table as CSV",
        csv,
        "trades_summary.csv",
        "text/csv",
        key=f"download_{title}",
    )

    # Create GridOptionsBuilder
    gb = GridOptionsBuilder.from_dataframe(trades_summary)

    # Enable row grouping for the 'Category' column
    gb.configure_column("Category", rowGroup=True, hide=True)

    # Configure grid options
    gb.configure_default_column(
        resizable=True, sortable=True, filterable=True, autoWidth=True
    )

    # Build grid options and expand all groups by default
    grid_options = gb.build()
    grid_options["groupDefaultExpanded"] = -1  # Expand all groups by default

    # Display the grid
    AgGrid(
        trades_summary,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        height=500,
        use_container_width=False,
        enable_enterprise_modules=True,  # Required for grouping
    )


def render_backtest_summary():
    selected_strategy, start_date, end_date = (
        fetch_user_selection_strategies_and_bt_dates()
    )
    st.markdown(
        f"<h6 style='text-align: left;'>Analysis for the strategy: {selected_strategy}</h6>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Date Range: `{start_date.strftime('%Y-%m-%d')}` to `{end_date.strftime('%Y-%m-%d')}`"
    )

    load_css_files()

    net_trades_summary = create_back_test_summary(
        selected_strategy, start_date, end_date, "Aggregated"
    )
    long_trades_summary = create_back_test_summary(
        selected_strategy, start_date, end_date, "Long"
    )
    short_trades_summary = create_back_test_summary(
        selected_strategy, start_date, end_date, "Short"
    )

    display_trade_summary(net_trades_summary, "Aggregated trades summary.")
    display_trade_summary(long_trades_summary, "Long only trades summary")
    display_trade_summary(short_trades_summary, "Short only trades summary")


if __name__ == "__main__":
    render_backtest_summary()
