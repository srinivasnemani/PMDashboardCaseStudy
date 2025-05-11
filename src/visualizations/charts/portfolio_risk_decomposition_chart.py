import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_portfolio_risk_decomposition(df: pd.DataFrame) -> go.Figure:
    """
    Create a visualization of portfolio risk decomposition.

    Parameters:
    df (pd.DataFrame): DataFrame containing risk decomposition data with columns:
        - Factor Risk (Annualized Variance)
        - Specific Risk (Annualized Variance)
        - Total Risk (Annualized Variance)
        - Factor Risk (Annualized Vol)
        - Specific Risk (Annualized Vol)
        - Total Risk (Annualized Vol)
        - Factor Risk Contribution %
        - Specific Risk Contribution %
        - Net Exposure Ratio

    Returns:
    go.Figure: Plotly figure showing risk decomposition
    """
    # Create a subplot figure with 1 row and 2 columns
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "bar"}, {"type": "pie"}]],
                        column_widths=[0.48, 0.48],
                        horizontal_spacing=0.08,
                        subplot_titles=("Risk Decomposition (Annualized Volatility)", "Risk Contribution % (Variance)")
    )

    # Bar Chart (Left) - Annualized Volatility metrics (as %)
    factor_vol = df["Factor Risk (Annualized Vol)"].iloc[0] * 100
    specific_vol = df["Specific Risk (Annualized Vol)"].iloc[0] * 100
    total_vol = df["Total Risk (Annualized Vol)"].iloc[0] * 100
    fig.add_trace(
        go.Bar(
            x=["Factor Risk", "Specific Risk", "Total Risk"],
            y=[factor_vol, specific_vol, total_vol],
            text=[f"{factor_vol:.2f}%", f"{specific_vol:.2f}%", f"{total_vol:.2f}%"],
            textposition='auto',
            name="Risk (Annualized Vol)",
            marker_color='#636EFA',
            showlegend=False
        ),
        row=1, col=1
    )

    # Pie Chart (Right) - Risk Contribution % (Volatility)
    factor_contrib = df["Factor Risk Contribution %"].iloc[0] * 100
    specific_contrib = df["Specific Risk Contribution %"].iloc[0] * 100
    fig.add_trace(
        go.Pie(
            labels=["Factor Risk Contribution", "Specific Risk Contribution"],
            values=[factor_contrib, specific_contrib],
            name="Risk Contribution %",
            hole=0.4,
            marker_colors=['#636EFA', '#EF553B'],
            textinfo='text',
            texttemplate='%{value:.2f}%',
        ),
        row=1, col=2
    )

    # Add borders around bar charts
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

    # Update layout
    fig.update_layout(
        width=1400,  # Wider format to fit screen
        height=600,
        title_text="Risk Breakdown: Factors Vs Idio",
        showlegend=True,
        margin=dict(l=40, r=40, t=80, b=40),
        xaxis_title="Risk Type",
        yaxis_title="Annualized Volatility (%)",
        yaxis=dict(tickformat=".2f%", ticksuffix="%"),
        # yaxis2 is not needed for pie chart
    )

    return fig


if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    data = {
        "Factor Risk (Annualized Variance)": [0.17574747],
        "Specific Risk (Annualized Variance)": [0.023790003],
        "Total Risk (Annualized Variance)": [0.199537473],
        "Factor Risk (Annualized Vol)": [0.419222],
        "Specific Risk (Annualized Vol)": [0.154239],
        "Total Risk (Annualized Vol)": [0.446696],
        "Factor Risk Contribution %": [0.880774259],
        "Specific Risk Contribution %": [0.119225741],
        "Net Exposure Ratio": [0.95]
    }
    df = pd.DataFrame(data)
    fig = plot_portfolio_risk_decomposition(df)
    fig.show()
