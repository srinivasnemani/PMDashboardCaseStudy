import pandas as pd
import plotly.graph_objects as go


def plot_factor_marginal_risk_contributions(df: pd.DataFrame) -> go.Figure:
    """
    Creates a Plotly bar chart with a dropdown to select different metrics
    for Factor Risk Contribution and Contribution %.

    Parameters:
    df (pd.DataFrame): DataFrame containing 'Factor', 'Risk Contribution', 'Contribution %' columns (as decimals).

    Returns:
    fig (go.Figure): Plotly figure object ready for display.
    """

    # Y-axis label mapping
    yaxis_labels = {
        "Risk Contribution": "Risk Contribution (%)",
        "Contribution %": "Contribution to PnL (%)",
    }

    # Y-axis tick format mapping (now correctly formatted as percentages)
    tickformats = {"Risk Contribution": ".2%", "Contribution %": ".2%"}

    # Single consistent bar color
    bar_color = "#636EFA"

    # Create the figure
    fig = go.Figure()

    # List of metrics
    metrics = ["Risk Contribution", "Contribution %"]
    for i, col in enumerate(metrics):
        fig.add_trace(
            go.Bar(
                x=df["Factor"],
                y=df[col],
                name=col,
                marker_color=bar_color,
                visible=(i == 0),  # Only first metric visible initially
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
                        "yaxis.tickformat": tickformats[col],
                    },
                ],
            )
        )

    # Update layout
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                x=0,  # Top-left (0 is left edge)
                xanchor="left",  # Anchor to left
                y=1.15,  # Place slightly above plot area
                yanchor="top",
                direction="down",
                showactive=True,
                bgcolor="mintcream",
                bordercolor="lightseagreen",
                borderwidth=2,
            )
        ],
        title={
            "text": "<b>Selected Metric: Risk Contribution</b>",
            "x": 0.5,  # Center title horizontally
            "xanchor": "center",
        },
        xaxis_title="Factor",
        yaxis_title="Risk Contribution (%)",
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    return fig


# Add main test block
if __name__ == "__main__":
    # To test the graph functionality before using it in dashboard.
    # Sample data where values are already in decimals (e.g., 53.44% -> 0.5344)
    data = {
        "Factor": [
            "Manuf",
            "BusEq",
            "Durbl",
            "NoDur",
            "Enrgy",
            "Telcm",
            "Hlth",
            "Chems",
            "Utils",
            "Money",
            "Other",
            "Shops",
        ],
        "Risk Contribution": [
            0.0497,
            0.0354,
            0.0082,
            0.0064,
            0.0014,
            0.0002,
            -0.0003,
            -0.0004,
            -0.0005,
            -0.0012,
            -0.0013,
            -0.0048,
        ],
        "Contribution %": [
            0.5344,
            0.3806,
            0.0884,
            0.0687,
            0.0151,
            0.0027,
            -0.0031,
            -0.0038,
            -0.0054,
            -0.0128,
            -0.0137,
            -0.0512,
        ],
    }

    # Create DataFrame
    df = pd.DataFrame(data)

    # Call the function
    fig = plot_factor_marginal_risk_contributions(df)

    # Display the figure
    fig.show()
