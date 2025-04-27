from sqlalchemy import text

from src.analytics.trade_summary import get_pnl_exposure_time_series
from src.data_access.crud_util import DataAccessUtil


def get_exposures_time_series(strategy_name, start_date, end_date):
    sql_query = f""" SELECT strategy_name, trade_open_date, ticker, shares, trade_open_price, 
                    direction, trade_close_date, trade_close_price 
                    FROM trade_booking tb where 
                    tb.strategy_name  = "{strategy_name}"
                    and tb.trade_open_date >= date('{start_date}')
                    and tb.trade_open_date <= date('{end_date}') """

    query_string = text(sql_query)
    trade_data_df = DataAccessUtil.fetch_data_from_db(query_string)
    result = get_pnl_exposure_time_series(trade_data_df)

    return result


def get_aum_leverage_ts(strategy_name, start_date, end_date):
    sql_query = f""" SELECT date, strategy_name, aum, target_leverage FROM aum_and_leverage aal where 
                    aal.strategy_name  = "{strategy_name}"
                    and aal.date >= date('{start_date}')
                    and aal.date <= date('{end_date}') """

    query_string = text(sql_query)
    aum_leverage_df = DataAccessUtil.fetch_data_from_db(query_string)
    return aum_leverage_df
