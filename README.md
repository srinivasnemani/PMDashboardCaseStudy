# Backtesting Dashboard

A Backtesting/portfolio management dashboard demo

### Docker

* 	A Docker image of this application is available here: [Docker image](https://hub.docker.com/r/mail2srinivasnemani/streamlit-backtest)

### Live Demo

*	The application is hosted and accessible at: [Live Demo](https://dashboardemo4-e2avdecjfuh7gdcx.westeurope-01.azurewebsites.net/)

## The code is divided into following modules

- **Data Management**
  - Data preparation and cleaning
  - Historical data access and management
  - Data storage and retrieval

- **Strategy Development**
  - Portfolio rebalancing
  - Backtesting capabilities

- **Portfolio Analysis**
  - Portfolio construction and optimization
  - Performance analytics and metrics
  - Risk attributions

- **Visualization**
  - Interactive dashboards for 
	-Performance charts and graphs
	- Risk metrics visualization

## Tech Stack

- **Core Technologies**
  - Python 3.13
  - Streamlit (Web Interface)
  - Pandas (Data Analysis)
  - NumPy (Numerical Computing)
  - SQLAlchemy (Database ORM)
  - PyTest

- **Data Analysis & Optimization**
  - CVXPY (Convex Optimization)
  - Statsmodels (Statistical Analysis)

- **Visualization**
  - Plotly
  - Plotly
  - Matplotlib
  - Seaborn

## Project Structure

```
src/
├── analytics/          # Performance and risk analytics
├── back_test/         # Strategy backtesting
├── data_access/       # Data retrieval and storage
├── data_prep/         # Data preparation and cleaning
├── portfolio_construction/  # Portfolio optimization
├── rebalance/         # Portfolio rebalancing
├── strategy/          # Trading strategies
└── visualizations/    # Data visualization components
```

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd PMDashboardCaseStudy
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the dashboard:
```bash
$env:PYTHONPATH = "The_Project_Folder_Path"
streamlit run .\src\visualizations\back_test_dashboard.py

```

2. Access the dashboard through your web browser at `http://localhost:8501`

## Development

- Code formatting: Black
- Linting: Ruff
- Testing: pytest
- Type checking: mypy

## Contributing



## License

	

## Contact

