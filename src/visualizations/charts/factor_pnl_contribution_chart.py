import pandas as pd
import plotly.graph_objects as go


def plot_factor_pnl_attributions(df: pd.DataFrame) -> go.Figure:
    """
    Creates a Plotly bar chart with a dropdown to select different metrics.

    Parameters:
    df (pd.DataFrame): DataFrame containing 'sector', 'factor_pnl_usd', 'factor_exposure_pct', 'pnl_contribution_pct' columns.

    Returns:
    fig (go.Figure): Plotly figure object ready for display.
    """

    # Y-axis label mapping
    yaxis_labels = {
        'factor_pnl_usd': "PnL (USD)",
        'factor_exposure_pct': "Exposure (%)",
        'pnl_contribution_pct': "PnL Contribution (%)"
    }

    # Y-axis tick format mapping
    tickformats = {
        'factor_pnl_usd': None,
        'factor_exposure_pct': ".6f",
        'pnl_contribution_pct': ".2%"
    }

    # Single consistent blue color
    bar_color = "#636EFA"

    # Create the figure
    fig = go.Figure()

    # Add bar traces for each metric
    metrics = ['factor_pnl_usd', 'factor_exposure_pct', 'pnl_contribution_pct']
    for i, col in enumerate(metrics):
        fig.add_trace(
            go.Bar(
                x=df['sector'],
                y=df[col],
                name=col,
                marker_color=bar_color,
                visible=(i == 0)  # Only first visible initially
            )
        )

    # Create dropdown buttons
    buttons = []
    for i, col in enumerate(metrics):
        visibility = [False] * len(metrics)
        visibility[i] = True
        buttons.append(
            dict(
                label=col,
                method="update",
                args=[
                    {"visible": visibility},
                    {
                        "title.text": f"<b>Selected Metric: {col}</b>",
                        "yaxis.title.text": yaxis_labels[col],
                        "yaxis.tickformat": tickformats[col]
                    }
                ]
            )
        )

    # Update layout
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                x=0,  # move to left
                xanchor="left",  # anchor at the left
                y=1.2,
                yanchor="top",
                direction="down",
                showactive=True,
                bgcolor="mintcream",
                bordercolor="lightseagreen",
                borderwidth=2
            )
        ],
        title={
            "text": "<b>Selected Metric: factor_pnl_usd</b>",
            "x": 0.5,  # center the title
            "xanchor": "center"  # anchor at center
        },
        xaxis_title="Sector",
        yaxis_title="PnL (USD)",
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40)
    )

    return fig


if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    # Example DataFrame
    df = pd.DataFrame({
        'sector': ['Manuf', 'BusEq', 'Other', 'Hlth', 'Utils', 'Durbl', 'Chems', 'Money', 'Telcm', 'Enrgy', 'NoDur',
                   'Residual', 'Shops'],
        'factor_pnl_usd': [4263264.377, 3398131.248, 3060318.995, 1628915.691, 1083469.537, 958075.7246, -2441.38994,
                           -14355.8558, -139862.219, -173392.953, -267022.735, -308487.447, -732199.106],
        'factor_exposure_pct': [1.66e-6, 1.63e-6, 1.26e-6, 2.94e-7, 3.72e-7, 1.33e-7, -1.32e-9, 2.15e-7, 5.96e-8,
                                6.08e-8, -5.87e-7, 0, -2.62e-7],
        'pnl_contribution_pct': [0.334257, 0.266427, 0.239941, 0.127714, 0.084948, 0.075117, -0.000191, -0.001013,
                                 -0.01096, -0.01359, -0.020094, -0.02419, -0.05741]
    })
    fig = plot_factor_pnl_attributions(df)
    fig.show()
