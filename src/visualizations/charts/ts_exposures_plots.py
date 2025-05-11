from typing import Literal

import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil


def render_exposure_time_series(df: pd.DataFrame, measure_type: Literal["USD", "Pct", "PnL"] = "USD") -> go.Figure:
    """
    Render a time series plot of exposures.

    Parameters:
    df (pd.DataFrame): DataFrame containing exposure data
    measure_type (str): Type of measure to plot ("USD", "Pct", or "PnL")

    Returns:
    go.Figure: Plotly figure showing exposure time series
    """
    # Plot it
    fig = go.Figure()
    if measure_type == "USD":
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['long_exposure'], mode='lines', name='Long Exposure'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['short_exposure'], mode='lines', name='Short Exposure'))
        fig.add_trace(
            go.Scatter(x=df['trade_open_date'], y=df['net_exposure'], mode='lines+markers', name='Net Exposure'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['total_exposure'], mode='lines', name='Gross Exposure'))
        y_axis_title = "Exposure (USD)"
        percentage_format = False
    elif measure_type == "Pct":
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['long_pnl_pct'], mode='lines', name='Long PnL %'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['short_pnl_pct'], mode='lines', name='Short PnL %'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['net_pnl_pct'], mode='lines+markers', name='Net PnL %'))
        y_axis_title = "PnL (Percentage)"
        percentage_format = True
    else:
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['long_pnl'], mode='lines', name='Long PnL'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['short_pnl'], mode='lines', name='Short PnL'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['total_pnl'], mode='lines+markers', name='Total PnL'))
        y_axis_title = "PnL (USD)"
        percentage_format = False

    # Base layout
    layout = {
        "xaxis_title": "Date",
        "yaxis_title": y_axis_title,
        "legend_title": "Exposure Type",
        "height": 600,
        "template": 'seaborn',
        "title": {"text": "Exposures Over Time", "x": 0.5, "xanchor": "center"}
    }

    # Add percentage formatting if needed
    if percentage_format:
        layout["yaxis"] = {
            "tickformat": ".1%",  # Format as percentage with 1 decimal place
            "hoverformat": ".2%"  # More precision on hover
        }

    fig.update_layout(**layout)
    return fig


def render_leverage_time_series(df: pd.DataFrame, measure_type: Literal["Leverage", "Capital", "Target Exposure"] = "Leverage") -> go.Figure:
    """
    Render a time series plot of leverage metrics.

    Parameters:
    df (pd.DataFrame): DataFrame containing leverage data
    measure_type (str): Type of measure to plot ("Leverage", "Capital", or "Target Exposure")

    Returns:
    go.Figure: Plotly figure showing leverage time series
    """
    # Plot it
    fig = go.Figure()
    if measure_type == "Leverage":
        fig.add_trace(go.Scatter(x=df['date'], y=df['target_leverage'], mode='lines', name='Target Leverage'))
        y_axis_title = "Leverage"
        plot_title = "Leverage Ratio"
    elif measure_type == "Capital":
        fig.add_trace(go.Scatter(x=df['date'], y=df['aum'], mode='lines', name='Capital'))
        y_axis_title = "Capital (USD)"
        plot_title = "Capital Allocations (USD)"
    elif measure_type == "Target Exposure":
        # Calculate target exposure dynamically
        df['calculated_target_exposure'] = df['aum'] * df['target_leverage']
        fig.add_trace(go.Scatter(x=df['date'], y=df['calculated_target_exposure'], mode='lines',
                                 name='Target Exposure (AUM × Leverage)'))
        y_axis_title = "Target Exposure (USD)"
        plot_title = "Gross Target Exposure (USD)"

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=y_axis_title,
        legend_title="Metric",
        height=600,
        template='seaborn',
        title={"text": plot_title, "x": 0.5, "xanchor": "center"}
    )
    return fig


if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    strategy_name = "MinVol"
    start_date = "2024-01-01"
    end_date = "2024-12-31"

    sql_query = f""" SELECT date, strategy_name, aum, target_leverage FROM aum_and_leverage aal where 
                    aal.strategy_name  = "{strategy_name}"
                    and aal.date >= date('{start_date}')
                    and aal.date <= date('{end_date}') """

    query_string = text(sql_query)
    trade_data = DataAccessUtil.fetch_data_from_db(query_string)
    # fig.show()
