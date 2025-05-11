import numpy as np
import pandas as pd
from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil


def get_pnl_time_series_from_trade_data(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate PnL in dollar terms and capital used
    df["trade_pnl"] = df["shares"] * (df["trade_close_price"] - df["trade_open_price"])
    df["trade_exposure"] = abs(df["shares"] * df["trade_open_price"])

    daily_pnl_usd = df.groupby("trade_open_date")["trade_pnl"].sum().reset_index()
    daily_capital = df.groupby("trade_open_date")["trade_exposure"].sum().reset_index()

    daily_result = pd.merge(daily_pnl_usd, daily_capital, on="trade_open_date")
    daily_result["trade_pnl_pct"] = (
        daily_result["trade_pnl"] / daily_result["trade_exposure"]
    )
    daily_result = daily_result.rename(columns={"trade_pnl": "trade_pnl_usd"})

    return daily_result[["trade_open_date", "trade_pnl_usd", "trade_pnl_pct"]]


def get_pnl_exposure_time_series(trade_data_df: pd.DataFrame) -> pd.DataFrame:
    # Calculate exposure (positive for long positions, negative for short positions)
    trade_data_df["exposure"] = (
        trade_data_df["shares"] * trade_data_df["trade_open_price"]
    )
    # Calculate PnL (shares * price difference)
    # - For long positions (positive shares), PnL is positive when close > open
    # - For short positions (negative shares), PnL is positive when close < open
    trade_data_df["pnl"] = trade_data_df["shares"] * (
        trade_data_df["trade_close_price"] - trade_data_df["trade_open_price"]
    )
    # Create a mask to identify long and short positions
    long_mask = trade_data_df["shares"] > 0
    short_mask = trade_data_df["shares"] < 0

    # Group by trade_open_date and calculate daily metrics
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

    # Time-weighted return calculations
    # 1. Calculate daily returns (avoiding division by zero)
    result["daily_long_return"] = np.where(
        result["long_exposure"] != 0, result["long_pnl"] / result["long_exposure"], 0
    )
    result["daily_short_return"] = np.where(
        result["short_exposure"].abs() != 0,
        result["short_pnl"] / result["short_exposure"].abs(),
        0,
    )
    result["daily_total_return"] = np.where(
        result["total_exposure"] != 0, result["total_pnl"] / result["total_exposure"], 0
    )

    # 2. Calculate cumulative returns using compounding (1+r)
    result["cumulative_long_pnl_pct"] = (1 + result["daily_long_return"]).cumprod() - 1
    result["cumulative_short_pnl_pct"] = (
        1 + result["daily_short_return"]
    ).cumprod() - 1
    result["cumulative_total_pnl_pct"] = (
        1 + result["daily_total_return"]
    ).cumprod() - 1

    # Replace NaN with 0 for dates with no exposure
    result["cumulative_long_pnl_pct"] = result["cumulative_long_pnl_pct"].fillna(0)
    result["cumulative_short_pnl_pct"] = result["cumulative_short_pnl_pct"].fillna(0)
    result["cumulative_total_pnl_pct"] = result["cumulative_total_pnl_pct"].fillna(0)

    result = result.reset_index()
    return result


def get_pnl_exposure_by_gics_sector(trade_data_df: pd.DataFrame) -> pd.DataFrame:
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

    grouped["pnl_pct"] = np.where(
        grouped["exposure"] != 0, grouped["pnl"] / grouped["exposure"], np.nan
    )

    grouped = grouped.sort_values(by=["gics_sector", "trade_open_date"])

    # Calculate cumulative sums by sector
    grouped["cumulative_pnl"] = grouped.groupby("gics_sector")["pnl"].cumsum()
    # grouped["cumulative_exposure"] = grouped.groupby("gics_sector")["exposure"].cumsum()
    grouped["cumulative_exposure"] = grouped.groupby("gics_sector")[
        "exposure"
    ].transform(lambda x: x.abs().cumsum())

    grouped["cumulative_pnl_pct"] = np.where(
        grouped["cumulative_exposure"] != 0,
        grouped["cumulative_pnl"] / grouped["cumulative_exposure"],
        np.nan,
    )

    return grouped


def fetch_pnl_by_gics_sector(
    strategy_name: str, start_date: str, end_date: str
) -> pd.DataFrame:
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


def get_pnl_exposure_ts_demo() -> pd.DataFrame:
    strategy_name = "Mom_RoC"
    start_date = "2024-01-01"
    end_date = "2024-12-31"

    sql_query = f""" SELECT * FROM trade_booking tb where
                    tb.strategy_name  = "{strategy_name}"
                    and tb.trade_open_date >= date('{start_date}')
                    and tb.trade_open_date <= date('{end_date}') """

    query_string = text(sql_query)
    trade_data_df = DataAccessUtil.fetch_data_from_db(query_string)
    result = get_pnl_exposure_time_series(trade_data_df)
    return result


if __name__ == "__main__":
    v1 = get_pnl_exposure_ts_demo()
    v1.to_clipboard()
    print(v1)
