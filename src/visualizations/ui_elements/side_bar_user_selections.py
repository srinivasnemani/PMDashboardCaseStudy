import pandas as pd
import streamlit as st
from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil
from src.data_access.sqllite_db_manager import TableNames


def get_strategies_list():
    tbl_name = TableNames.TRADE_BOOKING.value
    sql_query = f""" select distinct strategy_name  from {tbl_name} """

    query_string = text(sql_query)
    strategy_names_df = DataAccessUtil.fetch_data_from_db(query_string)
    return list(strategy_names_df['strategy_name'])


def get_back_test_date_range():
    tbl_name = TableNames.TRADE_BOOKING.value
    sql_query = f""" select date(min(trade_open_date )) as min_date, 
    date(max(trade_open_date )) as max_date  from {tbl_name}"""

    query_string = text(sql_query)
    strategy_names_df = DataAccessUtil.fetch_data_from_db(query_string)

    min_date = pd.to_datetime(strategy_names_df['min_date'].iloc[0]).strftime('%Y-%m-%d')
    max_date = pd.to_datetime(strategy_names_df['max_date'].iloc[0]).strftime('%Y-%m-%d')

    return [min_date, max_date]


def get_all_rebalance_dates():
    tbl_name = TableNames.TRADE_BOOKING.value
    sql_query = f""" select distinct trade_open_date as back_test_dates 
            from {tbl_name} """
    query_string = text(sql_query)

    df = DataAccessUtil.fetch_data_from_db(query_string)
    df['back_test_dates'] = pd.to_datetime(df['back_test_dates'])
    date_labels = sorted(df['back_test_dates'].dt.strftime('%Y-%m-%d').tolist(), reverse=True)
    # To test, remove this filtering later.
    date_labels = date_labels[5:-5]
    return date_labels


def fetch_user_selection_strategies_and_bt_dates():
    # Get the strategy list
    strategy_list = get_strategies_list()
    [start_date, end_date] = get_back_test_date_range()

    with st.sidebar:
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.header("Select a strategy")

        if strategy_list:
            current_strategy = st.radio(
                "Select a strategy",
                strategy_list,
                label_visibility="collapsed"
            )
        else:
            st.warning("No strategies available")
            current_strategy = None

        st.markdown('</div>', unsafe_allow_html=True)

        # Date picker section
        st.header("Date Range")
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input("Start Date", value=start_date)
        with col2:
            end_date = st.date_input("End Date", value=end_date)

        # Validate date range
        if start_date > end_date:
            st.error("Error: End date must be after start date")
    return current_strategy, start_date, end_date


def fetch_user_selection_strategies_and_one_bt_date():
    # Get the strategy list
    strategy_list = get_strategies_list()
    date_labels = get_all_rebalance_dates()

    with st.sidebar:
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.header("Select a strategy")

        if strategy_list:
            current_strategy = st.radio(
                "Select a strategy",
                strategy_list,
                label_visibility="collapsed"
            )
        else:
            st.warning("No strategies available")
            current_strategy = None

        st.markdown('</div>', unsafe_allow_html=True)

        # Date picker section
        st.header("Select a backtest date")
        selected_bt_date = st.selectbox("", date_labels)
    return current_strategy, selected_bt_date


def select_a_back_test_date():
    date_labels = get_all_rebalance_dates()

    st.markdown("<h5 style='font-weight: bold; color: #0096FF;'>Choose a date for risk decomposition analytics:</h5>",
                unsafe_allow_html=True)
    selected_date_str = st.selectbox("", date_labels)

    selected_date = pd.to_datetime(selected_date_str).date()
    st.write(f"You selected: {selected_date}")
    return selected_date


if __name__ == "__main__":
    v1 = select_a_back_test_date()
    print(v1)
