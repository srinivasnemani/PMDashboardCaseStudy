import os

import streamlit as st

# =============================================================================
# Delta Trade Analysis (To-Do)
# This page will provide analytics and visualizations for delta trade analysis:
# - Analysis of trade changes (delta) between rebalances or periods
# - Visualizations of new, closed, and adjusted trades
# - Interactive HTML content for detailed trade breakdowns
# =============================================================================

st.set_page_config(layout="wide")
st.markdown(
    "<h2 style='text-align: center;'>Delta Trade Analysis (To-Do)</h2>",
    unsafe_allow_html=True,
)

if __name__ == "__main__":
    # Read HTML content from file
    html_path = os.path.join(
        os.path.dirname(__file__), "..", "html_content", "delta_trade_analysis.html"
    )
    with open(html_path, "r") as f:
        html_content = f.read()

    # Render HTML content
    st.markdown(html_content, unsafe_allow_html=True)
