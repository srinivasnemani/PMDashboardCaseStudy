import streamlit as st

# =============================================================================
# Alpha Factor Attributions (To-Do)
# This page will provide analytics and visualizations for alpha factor attributions:
# - Brinson attributions (Allocation, Selection, Interaction effects)
# - Factor exposure, performance, and drawdown analysis
# - Attribution waterfall, style drift, and factor decay charts
# - Interactive filters for portfolio date, strategy, trade direction, sector, and region
# =============================================================================

st.set_page_config(layout="wide")
st.markdown(
    "<h2 style='text-align: center;'>Alpha Factor Attributions (To-Do)</h2>",
    unsafe_allow_html=True,
)

if __name__ == "__main__":
    st.markdown(
        """
        <div style="font-size:18px;">
        <br> Following visualizations/analytics can be added as part performance attribution. <br><br>
        
        <b>Brinson attributions</b> (Allocation, Selection and Interactions effects)<div style="font-size:12px;">
        In Long-Short portfolios Brinson attribution is less popular.</div> <br> 
        
        <br><h4><b>Alpha Factors Attribution Analysis</b></h4>
        <ul>
            <li><b>Factor Exposure Chart:</b> Showing portfolio's current exposure to each factor (if there is a benchmark, active or under weights against benchmark) </li>
            <li><b>Attribution Waterfall Chart:</b> Breaking down total alpha into contributions from each individual factor</li>
            <li><b>Residual Vs Explained Returns Breakdown</b></li>
            <li><b>Alpha Factor Performance Over Time:</b> Time series graph of alpha factors performance (For backtesting analysis)</li>
            <li><b>Factor Drawdowns Time Series:</b> To assess the drawdown periods and how long factors take to recover from drawdowns</li>
            <li><b>Style Drift Monitor:</b> Time series showing how factor exposures have evolved over time (For backtesting dashboard)</li>
            <li><b>Factor Decay Charts:</b> How quickly the factors decay (to monitor the trade turnovers)</li>
            <li><b>Factor Correlation Analysis Heat Maps:</b> How factor correlations behave during regime shifts</li>
            <br>The above charts and analytics can be sliced and diced into dollar amounts or percentage values
            
        </ul>
        <b><h4>Interactive Filters</h4></b>
        <ul style="list-style-type: none;">
            <li>&#10148; Portfolio Date (or date range) Selector</li>
            <li>&#10148; Strategy Selector</li>
            <li>&#10148; Trade Direction selector (Long/Short/Net)</li>
            <li>&#10148; Sector/Industry selections</li>
            <li>&#10148; Region/Country selections</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
