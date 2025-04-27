import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_risk_contribution_by_factor(df):
    # Convert decimals to percentages
    df["Risk Contribution"] = df["Risk Contribution"] * 100
    df["Contribution %"] = df["Contribution %"] * 100

    # Filter non-zero Contribution % for Pie and Risk Contribution for Bar
    df_nonzero_contrib = df[df["Contribution %"] != 0]
    df_nonzero_risk = df[df["Risk Contribution"] != 0]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "bar"}]],
        column_widths=[0.48, 0.48],
        horizontal_spacing=0.08,
        subplot_titles=("Contribution % Breakdown", "Risk Contribution")
    )

    # Pie Chart (Contribution %)
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

    # Define custom blue color from the image
    custom_blue = "rgba(102, 119, 255, 1)"  # Based on the blue shade you showed

    # Bar Chart (Risk Contribution %)
    fig.add_trace(
        go.Bar(
            x=df_nonzero_risk["Factor"],
            y=df_nonzero_risk["Risk Contribution"],
            text=[f"{val:.2f}%" for val in df_nonzero_risk["Risk Contribution"]],
            textposition='outside',
            name="Risk Contribution (%)",
            marker_color=custom_blue
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
        title_text="Portfolio Risk Contribution and Allocation Breakdown",
        showlegend=True,
    )

    fig.update_traces(marker_line_width=1.5, marker_line_color='white')

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
