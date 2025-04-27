import numpy as np
import pandas as pd
from src.data_access.crud_util import DataAccessUtil
from sqlalchemy import text


def get_pnl_time_series_from_trade_data(df):
    # Calculate PnL in dollar terms and capital used
    df["trade_pnl"] = df["shares"] * (df["trade_close_price"] - df["trade_open_price"])
    df["trade_exposure"] = abs(df["shares"] * df["trade_open_price"])

    # Calculate daily dollar PnL and capital
    daily_pnl_usd = df.groupby("trade_open_date")["trade_pnl"].sum().reset_index()
    daily_capital = df.groupby("trade_open_date")["trade_exposure"].sum().reset_index()

    # Merge to calculate percentage PnL
    daily_result = pd.merge(daily_pnl_usd, daily_capital, on="trade_open_date")
    daily_result["trade_pnl_pct"] = (
        daily_result["trade_pnl"] / daily_result["trade_exposure"]
    )
    daily_result = daily_result.rename(columns={"trade_pnl": "trade_pnl_usd"})

    return daily_result[["trade_open_date", "trade_pnl_usd", "trade_pnl_pct"]]


def get_pnl_exposure_time_series(trade_data_df):
    # Calculate exposure (positive for long positions, negative for short positions)
    trade_data_df["exposure"] = (
        trade_data_df["shares"] * trade_data_df["trade_open_price"]
    )

    # Calculate PnL (shares * price difference)
    # This is correct as is:
    # - For long positions (positive shares), PnL is positive when close > open
    # - For short positions (negative shares), PnL is positive when close < open
    trade_data_df["pnl"] = trade_data_df["shares"] * (
        trade_data_df["trade_close_price"] - trade_data_df["trade_open_price"]
    )

    # Create a mask to identify long and short positions
    long_mask = trade_data_df["shares"] > 0
    short_mask = trade_data_df["shares"] < 0

    result = (
        trade_data_df.groupby("trade_open_date")
        .agg(
            long_exposure=("exposure", lambda x: x[long_mask.loc[x.index]].sum()),
            short_exposure=("exposure", lambda x: x[short_mask.loc[x.index]].sum()),
            long_pnl=("pnl", lambda x: x[long_mask.loc[x.index]].sum()),
            short_pnl=("pnl", lambda x: x[short_mask.loc[x.index]].sum()),
        )
        .assign(
            total_exposure=lambda df: df["long_exposure"] + df["short_exposure"].abs(),
            net_exposure=lambda df: df["long_exposure"] + df["short_exposure"],
            total_pnl=lambda df: df["long_pnl"] + df["short_pnl"],
            long_pnl_pct=lambda df: np.where(
                df["long_exposure"] != 0, df["long_pnl"] / df["long_exposure"], np.nan
            ),
            short_pnl_pct=lambda df: np.where(
                df["short_exposure"] != 0,
                df["short_pnl"] / df["short_exposure"].abs(),
                np.nan,
            ),
            net_pnl_pct=lambda df: np.where(
                df["total_exposure"] != 0,
                df["total_pnl"] / df["total_exposure"],
                np.nan,
            ),
        )
    )

    # Add cumulative PnL columns in USD terms
    result["cumulative_long_pnl"] = result["long_pnl"].cumsum()
    result["cumulative_short_pnl"] = result["short_pnl"].cumsum()
    result["cumulative_total_pnl"] = result["total_pnl"].cumsum()

    # Add cumulative PnL columns in percentage terms
    # We need to calculate these carefully, as they're not simply the cumsum of percentages
    # For percentage, we need cumulative profit divided by cumulative exposure

    # First create temporary columns for cumulative exposures
    result["cum_long_exposure"] = result["long_exposure"].cumsum()
    result["cum_short_exposure"] = result["short_exposure"].abs().cumsum()
    result["cum_total_exposure"] = result["total_exposure"].cumsum()

    # Then calculate the cumulative percentage PnLs
    result["cumulative_long_pnl_pct"] = np.where(
        result["cum_long_exposure"] != 0,
        result["cumulative_long_pnl"] / result["cum_long_exposure"],
        np.nan,
    )

    result["cumulative_short_pnl_pct"] = np.where(
        result["cum_short_exposure"] != 0,
        result["cumulative_short_pnl"] / result["cum_short_exposure"],
        np.nan,
    )

    result["cumulative_total_pnl_pct"] = np.where(
        result["cum_total_exposure"] != 0,
        result["cumulative_total_pnl"] / result["cum_total_exposure"],
        np.nan,
    )

    # Drop temporary columns used for calculations
    result = result.drop(
        columns=["cum_long_exposure", "cum_short_exposure", "cum_total_exposure"]
    )

    # Reset index to return as a dataframe with trade_open_date as a column
    result = result.reset_index()

    return result


def get_pnl_exposure_by_gics_sector(trade_data_df):
    # Calculate exposure
    trade_data_df["exposure"] = (
        trade_data_df["shares"] * trade_data_df["trade_open_price"]
    )

    # Calculate PnL
    trade_data_df["pnl"] = trade_data_df["shares"] * (
        trade_data_df["trade_close_price"] - trade_data_df["trade_open_price"]
    )

    # Identify long and short positions
    trade_data_df["position_type"] = np.where(
        trade_data_df["shares"] > 0, "long", "short"
    )

    # Group by trade_open_date and GICS sector
    grouped = (
        trade_data_df.groupby(["trade_open_date", "gics_sector"])
        .agg(exposure=("exposure", "sum"), pnl=("pnl", "sum"))
        .reset_index()
    )

    # Calculate percentage PnL
    grouped["pnl_pct"] = np.where(
        grouped["exposure"] != 0, grouped["pnl"] / grouped["exposure"], np.nan
    )

    # Sort for cumulative calculation
    grouped = grouped.sort_values(by=["gics_sector", "trade_open_date"])

    # Calculate cumulative sums by sector
    grouped["cumulative_pnl"] = grouped.groupby("gics_sector")["pnl"].cumsum()
    grouped["cumulative_exposure"] = grouped.groupby("gics_sector")["exposure"].cumsum()

    # Calculate cumulative percentage PnL
    grouped["cumulative_pnl_pct"] = np.where(
        grouped["cumulative_exposure"] != 0,
        grouped["cumulative_pnl"] / grouped["cumulative_exposure"],
        np.nan,
    )

    return grouped


def fetch_pnl_by_gics_sector(strategy_name, start_date, end_date):
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
                AND tb.trade_open_date >= date('{start_date}')
                AND tb.trade_open_date <= date('{end_date}')
    """

    query_string = text(sql_query)
    trade_data_df = DataAccessUtil.fetch_data_from_db(query_string)
    result = get_pnl_exposure_by_gics_sector(trade_data_df)
    return result


# def get_pnl_exposure_ts_demo():
#     strategy_name = "MinVol"
#     start_date = "2024-01-01"
#     end_date = "2024-12-31"
#
#     sql_query = f""" SELECT * FROM trade_booking tb where
#                     tb.strategy_name  = "{strategy_name}"
#                     and tb.trade_open_date >= date('{start_date}')
#                     and tb.trade_open_date <= date('{end_date}') """
#
#     query_string = text(sql_query)
#     trade_data_df = DataAccessUtil.fetch_data_from_db(query_string)
#     result = get_pnl_exposure_time_series(trade_data_df)
#     return result


# if __name__ == "__main__":
#     v1 = get_pnl_exposure_ts_demo()
#     v1.to_clipboard()
