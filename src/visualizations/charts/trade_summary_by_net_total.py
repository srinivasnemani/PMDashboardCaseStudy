import pandas as pd
import plotly.graph_objects as go


def format_currency(value):
    """Format currency values in K, M, or B format."""
    abs_value = abs(value)
    if abs_value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif abs_value >= 1e6:
        return f"${value/1e6:.1f}M"
    elif abs_value >= 1e3:
        return f"${value/1e3:.1f}K"
    else:
        return f"${value:.0f}"

def plot_sector_exposure_by_total_and_net(df: pd.DataFrame) -> go.Figure:
    """
    Create a visualization of sector exposure analysis with multiple views.

    Parameters:
    df (pd.DataFrame): DataFrame containing sector exposure data with columns:
        - gics_sector: Sector names
        - gross_exposure_usd: Gross exposure in USD
        - net_exposure_usd: Net exposure in USD
        - gross_exposure_pct: Gross exposure as percentage
        - net_exposure_pct: Net exposure as percentage

    Returns:
    go.Figure: Plotly figure showing sector exposure analysis with dropdown menu
    """
    # Create all four figures with text labels
    fig_gross_exposure_usd = go.Bar(
        x=df['gics_sector'], 
        y=df['gross_exposure_usd'], 
        name='Gross Exposure USD',
        text=[format_currency(v) for v in df['gross_exposure_usd']],
        textposition='auto'
    )
    
    fig_net_exposure_usd = go.Bar(
        x=df['gics_sector'], 
        y=df['net_exposure_usd'], 
        name='Net Exposure USD',
        text=[format_currency(v) for v in df['net_exposure_usd']],
        textposition='auto'
    )
    
    fig_net_exposure_pct = go.Bar(
        x=df['gics_sector'], 
        y=df['net_exposure_pct'], 
        name='Net Exposure Pct',
        text=[f"{v:.2f}%" for v in df['net_exposure_pct']],
        textposition='auto'
    )

    # Create base figure
    fig = go.Figure()

    # Add all traces (initially make only first visible)
    fig.add_trace(fig_gross_exposure_usd)
    fig.add_trace(fig_net_exposure_usd)
    fig.add_trace(fig_net_exposure_pct)

    # Set visibility
    fig.data[0].visible = True
    for i in range(1, 3):
        fig.data[i].visible = False

    # Create dropdown with a light greenish border
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=list([
                    dict(label="Gross Exposure USD",
                         method="update",
                         args=[{"visible": [True, False, False]},
                               {"title": {"text": "<b>Gross Exposure (USD)</b>", "x": 0.5}, 
                                "xaxis": {"title": "Sectors"}, 
                                "yaxis": {"title": "USD", "tickformat": ",.2s"}}]),
                    dict(label="Net Exposure USD",
                         method="update",
                         args=[{"visible": [False, True, False]},
                               {"title": {"text": "<b>Net Exposure (USD)</b>", "x": 0.5}, 
                                "xaxis": {"title": "Sectors"}, 
                                "yaxis": {"title": "USD", "tickformat": ",.2s"}}]),
                    dict(label="Net Exposure %",
                         method="update",
                         args=[{"visible": [False, False, True]},
                               {"title": {"text": "<b>Net Exposure (%)</b>", "x": 0.5}, 
                                "xaxis": {"title": "Sectors"}, 
                                "yaxis": {"title": "Net Exposure (%)"}}]),
                ]),
                x=0,                # <-- Move dropdown to left
                xanchor="left",     # <-- Anchor to left
                y=1.2,
                yanchor="top",
                bordercolor="lightseagreen",
                borderwidth=2,
                bgcolor='mintcream'
            )
        ]
    )

    # Set layout
    fig.update_layout(
        title={
            "text": "<b>Sector Exposure Analysis</b>",
            "x": 0.5,
            "xanchor": "center"
        },
        xaxis_title="Sectors",
        yaxis_title="Value",
        yaxis_tickformat=",.2s",
        showlegend=False,
        uniformtext_minsize=8,  # Minimum text size
        uniformtext_mode='hide'  # Hide text if it doesn't fit
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
        'gross_exposure_usd': [
            6794352.75, 31565481.30, 46986853.11,
            26150870.63, 76481404.66, 35526668.58,
            58706068.89, 19092456.43, 43137117.64
        ],
        'net_exposure_usd': [
            -6794352.75, -31565481.30, 23916396.35,
            16052411.00, -3225924.46, -3977362.21,
            -44879676.37, 19092456.43, 31381716.03
        ],
        'gross_exposure_pct': [
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
