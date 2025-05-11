import pandas as pd
import plotly.graph_objects as go


def format_currency(value):
    """Format currency values in K, M, or B format."""
    abs_value = abs(value)
    if abs_value >= 1e9:
        return f"${value / 1e9:.1f}B"
    elif abs_value >= 1e6:
        return f"${value / 1e6:.1f}M"
    elif abs_value >= 1e3:
        return f"${value / 1e3:.1f}K"
    else:
        return f"${value:.0f}"


def plot_exposures_by_direction(df: pd.DataFrame) -> go.Figure:
    """
    Create a visualization of exposures by direction.

    Parameters:
    df (pd.DataFrame): DataFrame containing exposure data with columns:
        - gics_sector: Sector names
        - exposure: Net exposure values
        - exposure_pct: Exposure percentages

    Returns:
    go.Figure: Plotly figure showing exposures by direction
    """
    # Updated colors
    plotly_blue = '#1f77b4'
    orangish_red = '#ff7f0e'
    colors = [plotly_blue if val >= 0 else orangish_red for val in df['exposure']]

    # Main bar chart
    bar_chart = go.Bar(
        x=df['gics_sector'],
        y=df['exposure'],
        marker_color=colors,
        showlegend=False,
        text=[format_currency(v) for v in df['exposure']],
        textposition='auto'
    )

    # Dummy traces for manual legends
    long_legend = go.Bar(
        x=[None],
        y=[None],
        marker_color=plotly_blue,
        name='Long'
    )
    short_legend = go.Bar(
        x=[None],
        y=[None],
        marker_color=orangish_red,
        name='Short'
    )

    # Pie chart - initially hidden
    pie_chart = go.Pie(
        labels=df['gics_sector'],
        values=df['exposure_pct'],
        name='Exposure %',
        hole=0.3,
        showlegend=True,
        visible=False
    )

    # Build figure
    fig = go.Figure()
    fig.add_traces([bar_chart, long_legend, short_legend, pie_chart])

    # Dropdown for switching
    fig.update_layout(
        updatemenus=[{
            'buttons': [
                {
                    'label': 'Exposure (Bar)',
                    'method': 'update',
                    'args': [
                        {'visible': [True, True, True, False]},
                        {'title': {'text': 'Exposure by GICS Sector (Bar Chart)', 'x': 0.5, 'xanchor': 'center'},
                         'yaxis': {'title': 'Exposure'}}
                    ]
                },
                {
                    'label': 'Exposure % (Pie)',
                    'method': 'update',
                    'args': [
                        {'visible': [False, False, False, True]},
                        {'title': {'text': 'Gross Exposure % by GICS sector', 'x': 0.5, 'xanchor': 'center'}}
                    ]
                }
            ],
            'direction': 'down',
            'showactive': True,
            'x': 0,
            'xanchor': 'left',
            'y': 1.15,
            'yanchor': 'top',
            'bordercolor': 'lightseagreen',
            'borderwidth': 2,
            'bgcolor': 'mintcream'
        }],
        title={"text": "Exposure by GICS Sector", "x": 0.5, "xanchor": "center"},
        xaxis_title="GICS Sector",
        yaxis_title="Exposure",
        height=600,
        legend=dict(
            orientation="v",
            y=1,
            x=1,
            xanchor='right',
            yanchor='top',
            title="GICS Sector"
        ),
        uniformtext_minsize=8,  # Minimum text size
        uniformtext_mode='hide'  # Hide text if it doesn't fit
    )

    fig.update_yaxes(automargin=True)

    return fig


if __name__ == "__main__":
    data = {
        'gics_sector': [
            'Communication Services', 'Consumer Discretionary', 'Consumer Staples', 'Consumer Staples',
            'Financials', 'Financials', 'Health Care', 'Health Care', 'Industrials', 'Industrials',
            'Information Technology', 'Information Technology', 'Real Estate', 'Utilities', 'Utilities'
        ],
        'exposure': [
            -6794352.75, -31565481.3, 35451624.73, -11535228.38,
            21101640.81, -5049229.814, 36227740.11, -39853664.56,
            -15774653.18, -19752015.4, 6913196.257, -51739287.63,
            19092456.43, 37259416.83, -5877700.805
        ],
        'exposure_pct': [
            1.972572181, 9.164256342, 10.29250192, 3.348960898,
            6.126393207, 1.465918923, 10.63395791, 11.57052542,
            4.579716752, 5.734508867, 2.007075452, 15.0876378,
            5.543022244, 10.81734962, 1.706444973
        ]
    }
    df = pd.DataFrame(data)
    fig = plot_exposures_by_direction(df)
    fig.show()
