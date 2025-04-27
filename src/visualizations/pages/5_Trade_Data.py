import os

import streamlit as st

from src.visualizations.charts.trade_summary_by_direction_plot import \
    plot_exposures_by_direction
from src.visualizations.charts.trade_summary_by_net_total import \
    plot_sector_exposure_by_total_and_net
from src.visualizations.data_preparation.trade_data_analysis import \
    get_exposures_by_direction_net_total
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


def render_risk_attribution_page():
    load_css_files()

    # strategy_name, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()
    strategy_name, selected_date = fetch_user_selection_strategies_and_one_bt_date()
    st.subheader(f"Analysis for the strategy: {strategy_name} and for the date: {selected_date}")


def render_trade_summary_by_direction(exposures_summary_by_direction):
    st.subheader("Exposure by trade direction on the selected rebalance date.")
    tab_1, tab_2 = st.tabs(["Exposures by trade directions", "Table"])

    with tab_1:
        plotly_fig = plot_exposures_by_direction(exposures_summary_by_direction)
        st.plotly_chart(plotly_fig, use_container_width=True)

    with tab_2:
        st.dataframe(exposures_summary_by_direction, use_container_width=True)

def render_trade_summary_by_total_net(exposures_summary_by_direction):
    st.subheader("Exposure by trade direction on the selected rebalance.")
    tab_1, tab_2 = st.tabs(["Exposures by trade directions", "Table"])

    with tab_1:
        plotly_fig = plot_sector_exposure_by_total_and_net(exposures_summary_by_direction)
        st.plotly_chart(plotly_fig, use_container_width=True)

    with tab_2:
        st.dataframe(exposures_summary_by_direction, use_container_width=True)


def render_trade_data_analysis_page():
    load_css_files()

    # strategy_name, start_date, end_date = fetch_user_selection_strategies_and_bt_dates()
    strategy_name, selected_date = fetch_user_selection_strategies_and_one_bt_date()
    st.subheader(f"Analysis for the strategy: {strategy_name} and for the date: {selected_date}")

    [exposures_summary_by_direction, exposures_net_total] = get_exposures_by_direction_net_total(strategy_name,
                                                                                                 selected_date)
    render_trade_summary_by_direction(exposures_summary_by_direction)
    render_trade_summary_by_total_net(exposures_net_total)


if __name__ == "__main__":
    render_trade_data_analysis_page()
