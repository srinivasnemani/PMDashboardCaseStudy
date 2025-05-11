import os
import sys

import streamlit as st
from streamlit_tree_select import tree_select

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set page configuration
st.set_page_config(
    page_title="Backtest Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Read and inject custom CSS from external file in the visualizations/css_styles directory
css_path = os.path.join(os.path.dirname(__file__), 'css_styles/backtest_dashboard_styles.css')
with open(css_path, 'r') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Generate data

# App title
st.title("Backtest  Analysis Dashboard")
st.markdown("""
This dashboard is built for demo purpose to mimic the tools typically used by quantitative investment teams for portfolio management, strategy analysis, and backtesting evaluation.
* Currently, the following analytics (See the tree map below) are available in this dashboard.
* There are few To-Do list pages - refer to these pages for a list of improvements/extensions that can be added.
* Refer to the GitHub link for the code: [PMDashboardCaseStudy](https://github.com/srinivasnemani/PMDashboardCaseStudy)
* A Docker image of this application is available here: [Docker image](https://hub.docker.com/r/mail2srinivasnemani/streamlit-backtest)
""")

st.markdown("<br><h5>Index/List of visualizations implemented in the dashboard</h5>", unsafe_allow_html=True)

# Define the tree structure as nested dictionaries
nodes = [
    {
        "label": "1_Back Test Summary",
        "value": "back_test_summary",
        "children": [
            {
                "label": "Trade Summary Table (Aggregated, Long, Short)",
                "value": "trade_summary_table",
                "children": [
                    {
                        "label": "Return Based Metrics",
                        "value": "return_metrics",
                        "children": [
                            {"label": "Absolute Return", "value": "absolute_return"},
                            {"label": "Annualized Return", "value": "annualized_return"},
                            {"label": "Cumulative Return", "value": "cumulative_return"}
                        ]
                    },
                    {
                        "label": "Risk Adjusted Performance",
                        "value": "risk_adjusted",
                        "children": [
                            {"label": "Sharpe Ratio", "value": "sharpe_ratio"},
                            {"label": "Sortino Ratio", "value": "sortino_ratio"},
                            {"label": "Information Ratio", "value": "information_ratio"}
                        ]
                    },
                    {
                        "label": "Risk Measures",
                        "value": "risk_measures",
                        "children": [
                            {"label": "Volatility", "value": "volatility"},
                            {"label": "Beta", "value": "beta"},
                            {"label": "Alpha", "value": "alpha"},
                            {"label": "Tracking Error", "value": "tracking_error"}
                        ]
                    },
                    {
                        "label": "Drawdown Metrics",
                        "value": "drawdown_metrics",
                        "children": [
                            {"label": "Maximum Drawdown", "value": "maximum_drawdown"},
                            {"label": "Calmar Ratio", "value": "calmar_ratio"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "label": "2_Exposures Analysis (Per strategy, Time Period selection)",
        "value": "exposures_analysis",
        "children": [
            {
                "label": "Exposures Over Time (USD)",
                "value": "exposures_over_time"
            },
            {
                "label": "Capital, Leverage Over Time",
                "value": "capital_leverage",
                "children": [
                    {"label": "Leverage", "value": "leverage"},
                    {"label": "Capital", "value": "capital"},
                    {"label": "Target Exposure", "value": "target_exposure"}
                ]
            }
        ]
    },
    {
        "label": "3_Performance Analysis (Per strategy, Time Period selection)",
        "value": "performance_analysis",
        "children": [
            {
                "label": "P&L Over Time by Trade Direction",
                "value": "pnl_by_direction",
                "children": [
                    {
                        "label": "Time Series Charts for",
                        "value": "time_series_charts",
                        "children": [
                            {"label": "Cumulative P&L (USD)", "value": "cum_pnl_usd"},
                            {"label": "Cumulative P&L (Percentage)", "value": "cum_pnl_pct"},
                            {"label": "Daily P&L (USD)", "value": "daily_pnl_usd"},
                            {"label": "Daily P&L (Percentage)", "value": "daily_pnl_pct"}
                        ]
                    },
                    {"label": "Data Table", "value": "pnl_direction_table"}
                ]
            },
            {
                "label": "P&L Over Time by GICS Sectors",
                "value": "pnl_by_sector",
                "children": [
                    {
                        "label": "Time Series Chart",
                        "value": "sector_time_series",
                        "children": [
                            {"label": "Cumulative P&L (USD)", "value": "sector_cum_pnl_usd"},
                            {"label": "Cumulative P&L (Percentage)", "value": "sector_cum_pnl_pct"}
                        ]
                    },
                    {"label": "Data Table", "value": "pnl_sector_table"}
                ]
            }
        ]
    },
    {
        "label": "4_Risk Attributions (Per strategy, Rebalance Date selection)",
        "value": "risk_attributions",
        "children": [
            {
                "label": "Factor Exposures and PnL Decomposition",
                "value": "factor_exposures",
                "children": [
                    {
                        "label": "PnL Attributions Bar Charts",
                        "value": "pnl_attribution_charts",
                        "children": [
                            {"label": "Factor P&L (USD)", "value": "factor_pnl_usd"},
                            {"label": "Factor Exposure (Percentage)", "value": "factor_exposure_pct"},
                            {"label": "Factor P&L Contribution (Percentage)", "value": "factor_pnl_contrib_pct"}
                        ]
                    },
                    {"label": "Data Table", "value": "factor_exposures_table"}
                ]
            },
            {
                "label": "Risk Decomposition (Factors vs Idiosyncratic)",
                "value": "risk_decomposition",
                "children": [
                    {
                        "label": "Risk Decompositions",
                        "value": "risk_decomp_charts",
                        "children": [
                            {"label": "Risk Decomposition Annualized Volatility (Bar Chart)",
                             "value": "risk_decomp_vol"},
                            {"label": "Risk Variance Contribution (Pie Chart)", "value": "risk_variance_contrib"}
                        ]
                    },
                    {"label": "Data Table", "value": "risk_decomp_table"}
                ]
            },
            {
                "label": "Risk Contribution Breakdown by Factor",
                "value": "risk_contrib_breakdown",
                "children": [
                    {"label": "Factors Risk Decomposition (Pie Chart)", "value": "factors_risk_decomp"},
                    {"label": "Data Table", "value": "risk_contrib_table"}
                ]
            }
        ]
    },
    {
        "label": "5_Trade Data (Per strategy, Rebalance Date selection)",
        "value": "trade_data",
        "children": [
            {
                "label": "Exposure Analysis by Trade Direction",
                "value": "exposure_by_direction",
                "children": [
                    {"label": "Exposures by Trade Directions (Bar Chart)", "value": "exposures_direction_chart"},
                    {"label": "Gross Exposures by GICS Sector (Pie Chart)", "value": "gross_exposures_sector_chart"},
                    {"label": "Data Table", "value": "exposure_direction_table"}
                ]
            },
            {
                "label": "Exposure Analysis by Gross/Net",
                "value": "exposure_gross_net",
                "children": [
                    {"label": "Gross Exposures by GICS Sector USD (Bar Chart)", "value": "gross_exposures_sector_usd"},
                    {"label": "Net Exposures by GICS Sector USD (Bar Chart)", "value": "net_exposures_sector_usd"},
                    {"label": "Net Exposure by GICS Sector Percentages (Bar Chart)",
                     "value": "net_exposure_sector_pct"},
                    {"label": "Data Table", "value": "exposure_gross_net_table"}
                ]
            }
        ]
    }
]


# Function to extract all node values recursively for expansion
def get_all_node_values(nodes_list):
    all_values = []
    for node in nodes_list:
        all_values.append(node["value"])
        if "children" in node and node["children"]:
            all_values.extend(get_all_node_values(node["children"]))
    return all_values


def get_first_level_values(nodes_list):
    return [node["value"] for node in nodes_list]


# Get all node values for full expansion
all_node_values = get_all_node_values(nodes)

# Display the selected values
expanded_one_level = get_first_level_values(nodes)
selection = tree_select(nodes, expanded=expanded_one_level)
