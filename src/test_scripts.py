import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from dash import Input, Output, dash_table, dcc, html

# Mock data for sub-strategies
dates = pd.date_range(start='2025-01-01', end='2025-05-05', freq='D')
sub_strategies = ['Momentum', 'Value', 'Quality', 'Mean Reversion']
np.random.seed(42)
data = {strategy: np.random.normal(0, 0.02, len(dates)) for strategy in sub_strategies}
df_returns = pd.DataFrame(data, index=dates)
weights = {'Momentum': 0.25, 'Value': 0.25, 'Quality': 0.25, 'Mean Reversion': 0.25}
df_portfolio = pd.DataFrame({strategy: df_returns[strategy] * weights[strategy] for strategy in sub_strategies})
df_portfolio['Total'] = df_portfolio.sum(axis=1)

# Cumulative returns for visualization
df_cumulative = (1 + df_portfolio).cumprod() - 1

# Performance metrics
metrics = pd.DataFrame({
    'Strategy': sub_strategies,
    'Annualized Return (%)': [df_returns[strategy].mean() * 252 * 100 for strategy in sub_strategies],
    'Volatility (%)': [df_returns[strategy].std() * np.sqrt(252) * 100 for strategy in sub_strategies],
    'Sharpe Ratio': [(df_returns[strategy].mean() * 252) / (df_returns[strategy].std() * np.sqrt(252)) for strategy in
                     sub_strategies]
})

# Correlation matrix
corr_matrix = df_returns.corr()

# Initialize Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Long-Short Portfolio Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),

    html.H2("Sub-Strategy Return Contributions", style={'color': '#34495e'}),
    dcc.Graph(
        id='returns-chart',
        figure=px.area(
            df_cumulative,
            x=df_cumulative.index,
            y=sub_strategies,
            title="Cumulative Sub-Strategy Contributions to Portfolio Return",
            labels={'value': 'Cumulative Return', 'variable': 'Sub-Strategy'},
            template='plotly_white'
        ).update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
            legend_title="Sub-Strategy",
            hovermode="x unified"
        )
    ),
    html.Button("Download Chart as PNG", id="download-btn", n_clicks=0),
    dcc.Download(id="download-image"),

    html.H2("Performance Metrics", style={'color': '#34495e', 'marginTop': '20px'}),
    dash_table.DataTable(
        id='metrics-table',
        columns=[{"name": i, "id": i} for i in metrics.columns],
        data=metrics.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': '#ecf0f1', 'fontWeight': 'bold'},
        style_data={'backgroundColor': '#f9f9f9'}
    ),

    html.H2("Sub-Strategy Correlations", style={'color': '#34495e', 'marginTop': '20px'}),
    dcc.Graph(
        id='corr-heatmap',
        figure=px.imshow(
            corr_matrix,
            x=sub_strategies,
            y=sub_strategies,
            color_continuous_scale='RdBu',
            title="Correlation Matrix of Sub-Strategies",
            template='plotly_white'
        ).update_layout(
            xaxis_title="Sub-Strategy",
            yaxis_title="Sub-Strategy"
        )
    ),

    html.H2("Intraday Overlay (Placeholder)", style={'color': '#34495e', 'marginTop': '20px'}),
    html.P("Intraday data can be added with real-time API integration.", style={'color': '#7f8c8d'})
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff'})


# Callback for downloading the chart
@app.callback(
    Output("download-image", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True,
)
def download_chart(n_clicks):
    fig = px.area(
        df_cumulative,
        x=df_cumulative.index,
        y=sub_strategies,
        title="Cumulative Sub-Strategy Contributions to Portfolio Return",
        labels={'value': 'Cumulative Return', 'variable': 'Sub-Strategy'},
        template='plotly_white'
    ).update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        legend_title="Sub-Strategy",
        hovermode="x unified"
    )
    img_bytes = pio.to_image(fig, format="png")
    return dcc.send_bytes(img_bytes, "sub_strategy_contributions.png")


# Run server
if __name__ == '__main__':
    app.run_server(debug=True)