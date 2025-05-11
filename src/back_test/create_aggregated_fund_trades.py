from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil
from src.data_access.sqllite_db_manager import TableNames


def create_aggregated_fund_trades():
    """
    Creates aggregated fund trades by combining all non-AggregatedFund trades into a single AggregatedFund strategy.
    """
    trade_booking_tbl = TableNames.TRADE_BOOKING.value
    fetch_query = f"""
        SELECT *
        FROM {trade_booking_tbl}
        WHERE strategy_name != 'AggregatedFund'
    """
    query_string = text(fetch_query)
    trades_df = DataAccessUtil.fetch_data_from_db(query_string)

    if trades_df.empty:
        print("No trades found in the database")
        return

    trades_df['strategy_name'] = "AggregatedFund"

    delete_query = f"""
        DELETE FROM {trade_booking_tbl}
        WHERE strategy_name = 'AggregatedFund'
    """
    DataAccessUtil.execute_statement(delete_query)

    success = DataAccessUtil.store_dataframe_to_table(
        dataframe=trades_df,
        table_name=trade_booking_tbl,
        if_exists='append',
        index=False
    )

    if success:
        print(f"Successfully created aggregated fund trades with {len(trades_df)} entries")
    else:
        print("Failed to create aggregated fund trades")


if __name__ == "__main__":
    create_aggregated_fund_trades() 