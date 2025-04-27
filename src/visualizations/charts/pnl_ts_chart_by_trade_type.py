from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import text

from src.analytics.trade_summary import get_pnl_exposure_time_series
from src.data_access.crud_util import DataAccessUtil


def plot_pnl_series_by_trade_direction(df: pd.DataFrame, date_column: str = 'trade_open_date', height: int = 600, width: Optional[int] = None) -> go.Figure:
    """
    Create a PnL chart from the output of get_exposures_series_from_trade_data function.
    Shows Long, Short, and Total PnL with toggles between daily and cumulative views.

    Parameters:
    df (DataFrame): Output from get_exposures_series_from_trade_data
    date_column (str): Name of the date column
    height (int): Height of the chart
    width (int): Width of the chart (optional)

    Returns:
    plotly Figure: Interactive PnL chart
    """

    # Create figure
    fig = go.Figure()

    # Add traces for cumulative USD view
    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['cumulative_long_pnl'],
            name="Long (USD)",
            line=dict(color='#1f77b4', width=2),  # Blue
            visible=True,
            legendgroup='long',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['cumulative_short_pnl'],
            name="Short (USD)",
            line=dict(color='#d62728', width=2),  # Red
            visible=True,
            legendgroup='short',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['cumulative_total_pnl'],
            name="Total (USD)",
            line=dict(color='#2ca02c', width=2),  # Green
            visible=True,
            legendgroup='total',
            mode='lines'
        )
    )

    # Add traces for cumulative percentage view
    # Multiply percentage values by 100 to convert from decimal to percentage
    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['cumulative_long_pnl_pct'],  # Already in decimal form for tickformat
            name="Long (%)",
            line=dict(color='#1f77b4', width=2),  # Blue
            visible=False,
            legendgroup='long',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['cumulative_short_pnl_pct'],  # Already in decimal form for tickformat
            name="Short (%)",
            line=dict(color='#d62728', width=2),  # Red
            visible=False,
            legendgroup='short',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['cumulative_total_pnl_pct'],  # Already in decimal form for tickformat
            name="Total (%)",
            line=dict(color='#2ca02c', width=2),  # Green
            visible=False,
            legendgroup='total',
            mode='lines'
        )
    )

    # Add traces for daily USD view (non-cumulative)
    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['long_pnl'],
            name="Long Daily (USD)",
            line=dict(color='#1f77b4', width=2),  # Blue
            visible=False,
            legendgroup='long_daily',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['short_pnl'],
            name="Short Daily (USD)",
            line=dict(color='#d62728', width=2),  # Red
            visible=False,
            legendgroup='short_daily',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['total_pnl'],
            name="Total Daily (USD)",
            line=dict(color='#2ca02c', width=2),  # Green
            visible=False,
            legendgroup='total_daily',
            mode='lines'
        )
    )

    # Add traces for daily percentage view (non-cumulative)
    # Values are already in decimal form suitable for tickformat
    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['long_pnl_pct'],
            name="Long Daily (%)",
            line=dict(color='#1f77b4', width=2),  # Blue
            visible=False,
            legendgroup='long_daily',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['short_pnl_pct'],
            name="Short Daily (%)",
            line=dict(color='#d62728', width=2),  # Red
            visible=False,
            legendgroup='short_daily',
            mode='lines'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df['net_pnl_pct'],
            name="Total Daily (%)",
            line=dict(color='#2ca02c', width=2),  # Green
            visible=False,
            legendgroup='total_daily',
            mode='lines'
        )
    )

    # Create buttons for view toggles
    view_buttons = [
        dict(
            label="Cumulative USD",
            method="update",
            args=[
                {"visible": [True, True, True, False, False, False, False, False, False, False, False, False]},
                {
                    "title": dict(text="Cumulative PnL (USD)", x=0.5, xanchor="center"),
                    "yaxis.title.text": "PnL (USD)"
                }
            ]
        ),
        dict(
            label="Cumulative %",
            method="update",
            args=[
                {"visible": [False, False, False, True, True, True, False, False, False, False, False, False]},
                {
                    "title": dict(text="Cumulative PnL (%)", x=0.5, xanchor="center"),
                    "yaxis.title.text": "PnL (%)",
                    "yaxis.tickformat": ".1%"
                }
            ]
        ),
        dict(
            label="Daily USD",
            method="update",
            args=[
                {"visible": [False, False, False, False, False, False, True, True, True, False, False, False]},
                {
                    "title": dict(text="Daily PnL (USD)", x=0.5, xanchor="center"),
                    "yaxis.title.text": "PnL (USD)"
                }
            ]
        ),
        dict(
            label="Daily %",
            method="update",
            args=[
                {"visible": [False, False, False, False, False, False, False, False, False, True, True, True]},
                {
                    "title": dict(text="Daily PnL (%)", x=0.5, xanchor="center"),
                    "yaxis.title.text": "PnL (%)",
                    "yaxis.tickformat": ".1%"
                }
            ]
        )
    ]

    # Set up layout
    layout = dict(
        title=dict(text="Cumulative PnL (USD)", x=0.5, xanchor="center"),
        xaxis=dict(
            title="Date",
            rangeslider=dict(visible=True),
            type="date",
            showgrid=True,
            gridcolor='rgba(211, 211, 211, 0.4)',
            gridwidth=1
        ),
        yaxis=dict(
            title="PnL (USD)",
            showgrid=True,
            gridcolor='rgba(211, 211, 211, 0.4)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='rgba(0, 0, 0, 0.2)',
            zerolinewidth=1
        ),
        height=height,
        hovermode="x unified",
        legend=dict(orientation="v", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='white',
        autosize=True,
        margin=dict(l=50, r=25, b=50, t=70, pad=4),
        updatemenus=[
            dict(
                active=0,
                buttons=view_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.15,
                yanchor="top"
            )
        ]
    )

    if width is not None:
        layout['width'] = width

    fig.update_layout(layout)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(211, 211, 211, 0.4)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(211, 211, 211, 0.4)')

    return fig


if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    strategy_name = "MinVol"
    start_date = "2024-01-01"
    end_date = "2024-12-31"

    sql_query = f""" SELECT strategy_name, trade_open_date, ticker, shares, trade_open_price, 
                    direction, trade_close_date, trade_close_price 
                    FROM trade_booking tb where 
                    tb.strategy_name  = "{strategy_name}"
                    and tb.trade_open_date >= date('{start_date}')
                    and tb.trade_open_date <= date('{end_date}') """

    query_string = text(sql_query)
    df1 = DataAccessUtil.fetch_data_from_db(query_string)
    df2 = get_pnl_exposure_time_series(df1)

    fig = plot_pnl_series_by_trade_direction(df2)
    fig.show()
