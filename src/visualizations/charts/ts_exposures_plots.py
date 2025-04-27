import plotly.graph_objects as go
from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil


def render_exposure_time_series(df, measure_type="USD"):
    # Plot it
    fig = go.Figure()
    if measure_type == "USD":
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['long_exposure'], mode='lines', name='Long Exposure'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['short_exposure'], mode='lines', name='Short Exposure'))
        fig.add_trace(
            go.Scatter(x=df['trade_open_date'], y=df['net_exposure'], mode='lines+markers', name='Net Exposure'))
        fig.add_trace(go.Scatter(x=df['trade_open_date'], y=df['total_exposure'], mode='lines', name='Total Exposure'))
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
        "template": 'seaborn'
    }

    # Add percentage formatting if needed
    if percentage_format:
        layout["yaxis"] = {
            "tickformat": ".1%",  # Format as percentage with 1 decimal place
            "hoverformat": ".2%"  # More precision on hover
        }

    fig.update_layout(**layout)
    return fig


def render_leverage_time_series(df, measure_type="leverage"):
    # Plot it
    fig = go.Figure()
    if measure_type == "Leverage":
        fig.add_trace(go.Scatter(x=df['date'], y=df['target_leverage'], mode='lines', name='Target Leverage'))
        y_axis_title = "Leverage"
    elif measure_type == "Capital":  # Fixed syntax error by removing extra colon
        fig.add_trace(go.Scatter(x=df['date'], y=df['aum'], mode='lines', name='Capital'))
        y_axis_title = "Capital (USD)"
    elif measure_type == "Target Exposure":  # Fixed syntax error by removing extra colon
        # Calculate target exposure dynamically
        df['calculated_target_exposure'] = df['aum'] * df['target_leverage']
        fig.add_trace(go.Scatter(x=df['date'], y=df['calculated_target_exposure'], mode='lines',
                                 name='Target Exposure (AUM × Leverage)'))
        y_axis_title = "Target Exposure (USD)"

    # Add strategy name to titles if multiple strategies exist
    if len(df['strategy_name'].unique()) > 1:
        fig.update_layout(title=f"Multiple Strategies")
    else:
        fig.update_layout(title=f"Strategy: {df['strategy_name'].iloc[0]}")

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=y_axis_title,
        legend_title="Metric",
        height=600,
        template='seaborn'
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
