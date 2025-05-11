from sqlalchemy import text

from src.analytics.trade_summary import (get_pnl_exposure_by_gics_sector,
                                         get_pnl_exposure_time_series)
from src.data_access.crud_util import DataAccessUtil
from src.data_access.trade_booking import get_trade_and_sec_master_data


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