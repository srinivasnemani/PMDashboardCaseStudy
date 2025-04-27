import os
import sys

import streamlit as st

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set page configuration
st.set_page_config(
    page_title="Backtest Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for borders
st.markdown("""
    <style>
        .sidebar .block-container {
            border: 2px solid #ccc;
            border-radius: 8px;
            padding: 10px;
        }

        .stRadio, .stCheckbox, .stHeader, .stSubheader {
            border: 1px solid #aaa;
            border-radius: 5px;
            padding: 8px;
            margin-bottom: 10px;
        }

        .stDataFrame, .stTable {
            border: 2px solid #007ACC;
            border-radius: 8px;
            padding: 10px;
        }

        .element-container:has(.vega-embed) {
            border: 2px solid #28a745;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 20px;
        }

        .element-container {
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .stTabs > div > div {
            border: 2px solid #ccc;
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Generate data

# App title
st.title("Backtest  Analysis Dashboard")
st.markdown("Analyze the back test results  across various dimensions.")
