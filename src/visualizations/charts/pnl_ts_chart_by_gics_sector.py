import plotly.graph_objects as go
from sqlalchemy import text

from src.analytics.trade_summary import get_pnl_exposure_by_gics_sector
from src.data_access.crud_util import DataAccessUtil


def plot_ts_gics_sector_pnl(grouped_df):
    fig = go.Figure()

    # Dropdown options
    metrics = ['cumulative_pnl', 'cumulative_pnl_pct']
    labels = {'cumulative_pnl': 'Cumulative PnL (USD)', 'cumulative_pnl_pct': 'Cumulative PnL (%)'}

    # Add traces for each sector and metric
    for metric in metrics:
        for sector in grouped_df['gics_sector'].unique():
            df_sector = grouped_df[grouped_df['gics_sector'] == sector]
            fig.add_trace(go.Scatter(
                x=df_sector['trade_open_date'],
                y=df_sector[metric],
                mode='lines+markers',
                name=f'{sector}',
                visible=(metric == 'cumulative_pnl')  # Default visible metric
            ))

    # Buttons to switch between metrics
    buttons = []
    for i, metric in enumerate(metrics):
        visibility = [m == metric for m in metrics for _ in grouped_df['gics_sector'].unique()]
        buttons.append(dict(
            method='update',
            label=labels[metric],
            args=[{'visible': visibility},
                  {'title': f'{labels[metric]} by GICS Sector', 'yaxis': {'title': labels[metric]}}]
        ))

    fig.update_layout(
        updatemenus=[dict(
            buttons=buttons,
            direction='down',
            showactive=True,
            x=0,
            y=1.15,
            xanchor='left',
            yanchor='top'
        )],
        title='Cumulative PnL (USD) by GICS Sector',
        xaxis_title='Trade Open Date',
        yaxis_title='Cumulative PnL (USD)',
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


# Example usage:
# pnl_by_sector_df = get_pnl_exposure_by_sector(trade_data_df)
# plot_cumulative_pnl(pnl_by_sector_df)
# Example usage:
# 1. Process the data to add sector-specific calculations
# processed_df = prepare_sector_data(df)
#
# 2. Create chart showing performance of each sector
# fig = create_sector_breakdown_chart(processed_df)
#
# 3. Create the original chart with option to group by sector
# fig = create_pnl_time_series_chart(df, group_by_sector=True)

if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    strategy_name = "MinVol"
    start_date = "2024-01-01"
    end_date = "2024-12-31"

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
    df = get_pnl_exposure_by_gics_sector(trade_data_df)
    fig = plot_ts_gics_sector_pnl(df)
    fig.show()