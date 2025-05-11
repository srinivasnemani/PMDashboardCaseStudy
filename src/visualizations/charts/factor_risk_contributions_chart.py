import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_risk_contribution_by_factor(df):
    # Convert decimals to percentages
    df["Risk Contribution"] = df["Risk Contribution"] * 100
    df["Contribution %"] = df["Contribution %"] * 100

    # Filter non-zero Contribution % for Pie and Risk Contribution for Bar
    df_nonzero_contrib = df[(df["Contribution %"] != 0) & (df["Factor"] != "Total")]
    df_nonzero_risk = df[(df["Risk Contribution"] != 0) & (~df["Factor"].isin(["Total", "Specific Risk"]))]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "bar"}]],
        column_widths=[0.48, 0.48],
        horizontal_spacing=0.08,
        subplot_titles=("Factor Risk Decomposition (% of Gross Absolute Contributions)", "Active Factor Tilts")
    )

    # Pie Chart (Contribution %), exclude 'Total' row
    fig.add_trace(
        go.Pie(
            labels=df_nonzero_contrib["Factor"],
            values=df_nonzero_contrib["Contribution %"],
            name="Contribution %",
            hole=0.4,
            textinfo='percent+label'
        ),
        row=1, col=1
    )

    # Assign a unique color to each sector/factor
    unique_factors = df_nonzero_risk["Factor"].unique()
    color_palette = [
        '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692',
        '#B6E880', '#FF97FF', '#FECB52', '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728',
        '#9467BD', '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF'
    ]
    factor_colors = {factor: color_palette[i % len(color_palette)] for i, factor in enumerate(unique_factors)}
    bar_colors = [factor_colors[f] for f in df_nonzero_risk["Factor"]]

    # Horizontal Bar Chart (Portfolio Exposure only, one bar per sector)
    if "Portfolio Exposure" in df_nonzero_risk.columns:
        fig.add_trace(
            go.Bar(
                x=df_nonzero_risk["Portfolio Exposure"],
                y=df_nonzero_risk["Factor"],
                orientation='h',
                name="Portfolio Exposure",
                marker_color=bar_colors,
                showlegend=True,
                legendgroup="sector",
                # Custom legend items for each sector
                customdata=df_nonzero_risk["Factor"],
                hovertemplate='<b>%{y}</b><br>Exposure: %{x}<extra></extra>'
            ),
            row=1, col=2
        )

    # Border boxes
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=0.48, y1=1,
        xref="paper", yref="paper",
        line=dict(color="LightGreen", width=1)
    )
    fig.add_shape(
        type="rect",
        x0=0.52, y0=0, x1=1, y1=1,
        xref="paper", yref="paper",
        line=dict(color="LightGreen", width=1)
    )

    fig.update_layout(
        width=1400,
        height=600,
        title_text="Risk Attribution & Factor Tilt Analysis",
        showlegend=True,
        barmode='group',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.18,
            title="Sectors",
            font=dict(size=13),
            traceorder="normal"
        )
    )

    fig.update_traces(marker_line_width=1.5, marker_line_color='white')

    return fig

def plot_portfolio_factor_exposures(df):
    """
    Plots a horizontal bar chart of Portfolio Factor Exposures (Active Bets).
    Parameters:
        df (pd.DataFrame): DataFrame containing 'Factor' and 'Portfolio Exposure' columns.
    Returns:
        fig (go.Figure): Plotly figure object.
    """
    # Exclude 'Total' and 'Specific Risk' if present
    df_plot = df[~df['Factor'].isin(['Total', 'Specific Risk'])]
    fig = go.Figure(
        go.Bar(
            y=df_plot['Factor'],
            x=df_plot['Portfolio Exposure'],
            orientation='h',
            marker_color='black',
            name='Factor Exposure',
        )
    )
    fig.update_layout(
        title='Portfolio Factor Exposures (Active Bets)',
        xaxis_title='Factor Exposure',
        yaxis_title='',
        height=500,
        margin=dict(l=120, r=40, t=60, b=40),
        plot_bgcolor='white',
    )
    return fig

if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    # Your decimal data
    data = {
        "Factor": [
            "Manuf", "BusEq", "Specific Ri", "Durbl", "NoDur",
            "Enrgy", "Telcm", "Hlth", "Chems", "Utils",
            "Money", "Other", "Shops"
        ],
        "Risk Contribution": [
            0.04975, 0.03543, 0.01221, 0.00822, 0.00640,
            0.00141, 0.00025, -0.00029, -0.00035, -0.00050,
            -0.00119, -0.00127, -0.00476
        ],
        "Contribution %": [
            0.47246, 0.33646, 0.11597, 0.07810, 0.06074,
            0.01336, 0.00237, -0.00278, -0.00333, -0.00473,
            -0.01132, -0.01209, -0.04522
        ]
    }
    df = pd.DataFrame(data)
    fig = plot_risk_contribution_by_factor(df)
    fig.show()
