import os

import streamlit as st

st.set_page_config(layout="wide")


if __name__ == "__main__":
    # Read HTML content from file
    html_path = os.path.join(os.path.dirname(__file__), '..', 'html_content', 'ux_improvements.html')
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Render HTML content
    st.markdown(html_content, unsafe_allow_html=True)