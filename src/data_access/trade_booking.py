from sqlalchemy import MetaData, Table
from sqlalchemy.sql import and_, delete, or_, text

from src.data_access.crud_util import DataAccessUtil
from src.data_access.sqllite_db_manager import TableNames, get_db_engine


def get_trade_and_sec_master_data(strategy_name, start_date, end_date):
    if start_date == end_date:
        end_date = None

    sql_query = f"""
        SELECT
            tb.*,
            sm.security,
            sm.gics_sector,
            sm.ff12industry
        FROM
            trade_booking tb
        JOIN
            sp500_sec_master sm ON tb.ticker = sm.symbol
        WHERE
            tb.strategy_name = "{strategy_name}"
            AND date(tb.trade_open_date) {f"= date('{start_date}')" if end_date is None else f">= date('{start_date}') AND date(tb.trade_open_date) <= date('{end_date}')"}
    """

    query_string = text(sql_query)
    trade_data_df = DataAccessUtil.fetch_data_from_db(query_string)
    return trade_data_df


def update_trades(trades_df):
    #     Trade Closing

    db_engine = get_db_engine()
    if trades_df.empty:
        # First rebalance, no previous trades to close.
        return

    # needed to work with the date formatting's of sql alchemy. Can be improved later
    if trades_df['trade_open_date'].dtype == 'datetime64[ns]':
        trades_df['trade_open_date'] = trades_df['trade_open_date'].dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'date' in trades_df.columns:
        trades_df = trades_df.drop('date', axis=1)

    TRADE_BOOKING_TABLE = TableNames.TRADE_BOOKING.value
    # Create metadata and reflect table
    metadata = MetaData()
    table = Table(TRADE_BOOKING_TABLE, metadata, autoload_with=db_engine)
    id_columns_trade_booking = ['strategy_name', 'trade_open_date', 'ticker', 'direction']
    key_values = trades_df[id_columns_trade_booking].to_records(index=False)

    delete_stmt = delete(table).where(
        # Create delete statement for each combination of values
        or_(*[
            and_(
                table.c.strategy_name == row[0],
                table.c.trade_open_date == row[1],
                table.c.ticker == row[2],
                table.c.direction == row[3]
            ) for row in key_values
        ])
    )

    # Remove the previous rebalance records first and update them back with the closing prices.
    with db_engine.begin() as conn:
        conn.execute(delete_stmt)
        trades_df.to_sql(TRADE_BOOKING_TABLE, conn, if_exists='append', index=False)


if __name__ == "__main__":
    print("test")
