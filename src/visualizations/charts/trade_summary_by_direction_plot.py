import pandas as pd
import plotly.graph_objects as go


def plot_exposures_by_direction(df: pd.DataFrame) -> go.Figure:
    """
    Plot a bar and pie chart with a dropdown to switch between
    exposure and exposure_pct visualizations.
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
        showlegend=False
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
        showlegend=False,
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
                        {'title': 'Exposure by GICS Sector (Bar Chart)',
                         'yaxis': {'title': 'Exposure'}}
                    ]
                },
                {
                    'label': 'Exposure % (Pie)',
                    'method': 'update',
                    'args': [
                        {'visible': [False, False, False, True]},
                        {'title': 'Exposure % by GICS Sector (Pie Chart)'}
                    ]
                }
            ],
            'direction': 'down',
            'showactive': True,
        }],
        title="Exposure by GICS Sector",
        xaxis_title="GICS Sector",
        yaxis_title="Exposure",
        height=600,
        legend=dict(
            orientation="h",
            y=1.15,
            x=0.5,
            xanchor='center',
            yanchor='bottom'
        )
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
