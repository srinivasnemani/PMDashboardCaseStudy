import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.visualizations.data_preparation.backtest_summary import \
    create_back_test_summary
from src.visualizations.ui_elements.side_bar_user_selections import \
    fetch_user_selection_strategies_and_bt_dates

# Append project root to sys.path


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


def create_format_map():
    return {
        'Absolute Return': '{:.2%}',
        'Annualized Return': '{:.2%}',
        'Cumulative Return': '{:.2%}',
        'Sharpe Ratio': '{:.2f}',
        'Sortino Ratio': '{:.2f}',
        'Information Ratio': '{:.2f}',
        'Volatility': '{:.2%}',
        'Beta': '{:.2f}',
        'Alpha': '{:.2%}',
        'Maximum Drawdown': '{:.2%}',
        'Calmar Ratio': '{:.2f}'
    }


def display_trade_summary(trades_summary, title, format_map):
    st.subheader(title)
    styled_html = trades_summary.style.format(format_map).to_html(classes='dataframe')
    st.write(styled_html, unsafe_allow_html=True)


def render_backtest_summary():

    st.set_page_config(layout="wide")
    selected_strategy, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()
    st.subheader(f"Analysis for the strategy: {selected_strategy}")
    st.markdown(f"Date Range: `{start_date.strftime('%Y-%m-%d')}` to `{end_date.strftime('%Y-%m-%d')}`")

    load_css_files()

    net_trades_summary = create_back_test_summary(selected_strategy, start_date, end_date, "Aggregated")
    long_trades_summary = create_back_test_summary(selected_strategy, start_date, end_date, "Long")
    short_trades_summary = create_back_test_summary(selected_strategy, start_date, end_date, "Short")

    format_map = create_format_map()

    display_trade_summary(net_trades_summary, "Aggregated trades summary.", format_map)
    display_trade_summary(long_trades_summary, "Long only trades summary", format_map)
    display_trade_summary(short_trades_summary, "Short only trades summary", format_map)


if __name__ == "__main__":
    render_backtest_summary()
