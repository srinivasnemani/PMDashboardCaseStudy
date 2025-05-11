# Visualizations Analytics Tree Map

This document provides an overview of all analytics and visualizations available in the `src/visualizations/pages` directory, organized as a tree map.

---

## Pages and Analytics

```
1 Back_Test_Summary.py
├── Trade Summary Table (Aggregated, Long, Short)
│   └── Metrics: Absolute Return, Annualized Return, Cumulative Return, Volatility, Maximum Drawdown, Sharpe Ratio, Sortino Ratio, Information Ratio, Calmar Ratio, Beta, Alpha

2 Exposures_Analysis
├── Exposures Over Time (USD)
├── Capital, Leverage Over Time
│   ├── Leverage
│   ├── Capital
│   └── Target Exposure

3 Performance Analysis
├── P&L Over Time by Trade Direction
│   ├── Time Series Chart
│   └── Table View
├── P&L Over Time by GICS Sectors
│   ├── Time Series Chart
│   └── Table View

4 Risk_Attributions.py
├── Factor Exposures and PnL Decomposition
│   ├── PnL Attributions Chart
│   └── Table View
├── Risk Decomposition (Factors vs Idiosyncratic)
│   ├── Risk Decomposition Chart
│   └── Table View
├── Risk Contribution Breakdown by Factor
│   ├── Factors Contributions Chart
│   └── Table View

5 Trade_Data.py
├── Exposure Analysis by Trade Direction
│   ├── Exposures by Trade Directions Chart
│   └── Table View
├── Exposure Analysis by Total/Net
│   ├── Exposures by Total/Net Chart
│   └── Table View
```

---

## How to Use
- Each page provides interactive analytics and visualizations using Streamlit and AG Grid.
- Download options are available for all tables.
- Use the sidebar to select strategies and date ranges where applicable.

---

*This tree map helps you quickly understand the analytics and visualizations available in each dashboard page.* 