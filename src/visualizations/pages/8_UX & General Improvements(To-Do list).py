import os

import streamlit as st

# =============================================================================
# UX & General Improvements (To-Do List)
# This page will track and display planned user experience and general improvements:
# - List of UI/UX enhancements and feature requests
# - General improvements for dashboards and analytics
# - Interactive HTML content for improvement tracking
# =============================================================================

st.set_page_config(layout="wide")
st.markdown(
    "<h2 style='text-align: center;'>UX & General Improvements (To-Do List)</h2>",
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    # Read HTML content from file
    html_path = os.path.join(
        os.path.dirname(__file__), "..", "html_content", "ux_improvements.html"
    )
    with open(html_path, "r") as f:
        html_content = f.read()

    # Render HTML content
    st.markdown(html_content, unsafe_allow_html=True)
