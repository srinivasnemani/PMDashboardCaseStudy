import pandas as pd
import plotly.graph_objects as go


def plot_sector_exposure_by_total_and_net(df: pd.DataFrame) -> go.Figure:
    """
    Create a visualization of sector exposure analysis with multiple views.

    Parameters:
    df (pd.DataFrame): DataFrame containing sector exposure data with columns:
        - gics_sector: Sector names
        - absolute_exposure_usd: Absolute exposure in USD
        - net_exposure_usd: Net exposure in USD
        - absolute_exposure_pct: Absolute exposure as percentage
        - net_exposure_pct: Net exposure as percentage

    Returns:
    go.Figure: Plotly figure showing sector exposure analysis with dropdown menu
    """
    # Create all four figures
    fig_absolute_exposure_usd = go.Bar(x=df['gics_sector'], y=df['absolute_exposure_usd'], name='Absolute Exposure USD')
    fig_net_exposure_usd = go.Bar(x=df['gics_sector'], y=df['net_exposure_usd'], name='Net Exposure USD')
    fig_absolute_exposure_pct = go.Pie(labels=df['gics_sector'], values=df['absolute_exposure_pct'], name='Absolute Exposure Pct')
    fig_net_exposure_pct = go.Bar(x=df['gics_sector'], y=df['net_exposure_pct'], name='Net Exposure Pct')

    # Create base figure
    fig = go.Figure()

    # Add all traces (initially make only first visible)
    fig.add_trace(fig_absolute_exposure_usd)
    fig.add_trace(fig_net_exposure_usd)
    fig.add_trace(fig_absolute_exposure_pct)
    fig.add_trace(fig_net_exposure_pct)

    # Set visibility
    fig.data[0].visible = True
    for i in range(1, 4):
        fig.data[i].visible = False

    # Create dropdown with a light greenish border
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=list([
                    dict(label="Absolute Exposure USD",
                         method="update",
                         args=[{"visible": [True, False, False, False]},
                               {"title": {"text": "Absolute Exposure (USD)", "x": 0.5}, "xaxis": {"title": "Sectors"}, "yaxis": {"title": "USD", "tickformat": ",.2s"}}]),
                    dict(label="Net Exposure USD",
                         method="update",
                         args=[{"visible": [False, True, False, False]},
                               {"title": {"text": "Net Exposure (USD)", "x": 0.5}, "xaxis": {"title": "Sectors"}, "yaxis": {"title": "USD", "tickformat": ",.2s"}}]),
                    dict(label="Absolute Exposure %",
                         method="update",
                         args=[{"visible": [False, False, True, False]},
                               {"title": {"text": "Absolute Exposure (%)", "x": 0.5}}]),
                    dict(label="Net Exposure %",
                         method="update",
                         args=[{"visible": [False, False, False, True]},
                               {"title": {"text": "Net Exposure (%)", "x": 0.5}, "xaxis": {"title": "Sectors"}, "yaxis": {"title": "%"}}]),
                ]),
                x=0,                # <-- Move dropdown to left
                xanchor="left",     # <-- Anchor to left
                y=1.2,
                yanchor="top",
                bordercolor="lightgreen",
                borderwidth=2
            )
        ]
    )

    # Set layout
    fig.update_layout(
        title={
            "text": "Sector Exposure Analysis",
            "x": 0.5,
            "xanchor": "center"
        },
        xaxis_title="Sectors",
        yaxis_title="Value",
        yaxis_tickformat=",.2s",
        showlegend=False
    )

    return fig


if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    # Data preparation
    data = {
        'gics_sector': [
            'Communication Services', 'Consumer Discretionary', 'Consumer Staples',
            'Financials', 'Health Care', 'Industrials', 'Information Technology',
            'Real Estate', 'Utilities'
        ],
        'absolute_exposure_usd': [
            6794352.75, 31565481.30, 46986853.11,
            26150870.63, 76481404.66, 35526668.58,
            58706068.89, 19092456.43, 43137117.64
        ],
        'net_exposure_usd': [
            -6794352.75, -31565481.30, 23916396.35,
            16052411.00, -3225924.46, -3977362.21,
            -44879676.37, 19092456.43, 31381716.03
        ],
        'absolute_exposure_pct': [
            1.97, 9.16, 13.64, 7.59, 22.20, 10.31,
            17.04, 5.54, 12.52
        ],
        'net_exposure_pct': [
            -1.97, -9.16, 6.94, 4.66, -0.94, -1.15,
            -13.03, 5.54, 9.11
        ]
    }

    df = pd.DataFrame(data)

    # Create and show figure
    fig = plot_sector_exposure_by_total_and_net(df)
    fig.show()
