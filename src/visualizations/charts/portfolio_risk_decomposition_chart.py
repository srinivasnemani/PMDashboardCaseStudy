import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_portfolio_risk_decomposition(df: pd.DataFrame) -> go.Figure:
    """
    Create a visualization of portfolio risk decomposition.

    Parameters:
    df (pd.DataFrame): DataFrame containing risk decomposition data with columns:
        - Factor Risk
        - Specific Risk
        - Total Risk
        - Factor %
        - Specific %

    Returns:
    go.Figure: Plotly figure showing risk decomposition
    """
    factor_risk_pct = df["Factor Risk"].iloc[0]
    specific_risk_pct = df["Specific Risk"].iloc[0]
    total_risk_pct = df["Total Risk"].iloc[0]

    factor_pct = df["Factor %"].iloc[0]
    specific_pct = df["Specific %"].iloc[0]

    # Create a subplot figure with 1 row and 2 columns
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "bar"}, {"type": "domain"}]],
                        column_widths=[0.48, 0.48],
                        horizontal_spacing=0.08,
                        subplot_titles=("Factor, Specific & Total Risk (%)", "Factor vs Specific %"))

    # Bar Chart (Left)
    fig.add_trace(
        go.Bar(
            x=["Factor Risk", "Specific Risk", "Total Risk"],
            y=[factor_risk_pct * 100, specific_risk_pct * 100, total_risk_pct * 100],
            text=[f"{factor_risk_pct * 100:.2f}%", f"{specific_risk_pct * 100:.2f}%", f"{total_risk_pct * 100:.2f}%"],
            textposition='auto',
            name="Risk (%)"
        ),
        row=1, col=1
    )

    # Pie Chart (Right)
    fig.add_trace(
        go.Pie(
            labels=["Factor %", "Specific %"],
            values=[factor_pct, specific_pct],
            name="Risk %",
            hole=0.4
        ),
        row=1, col=2
    )

    # Add borders around bar and pie charts
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
        showlegend=True
    )

    return fig


if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    data = {
        "Factor Risk": [0.17574747],
        "Specific Risk": [0.023790003],
        "Total Risk": [0.199537473],
        "Factor %": [0.880774259],
        "Specific %": [0.119225741]
    }
    df = pd.DataFrame(data)
    fig = plot_portfolio_risk_decomposition(df)
    fig.show()
