"""Homepage of Streamlit App"""

import streamlit as st

st.set_page_config(
    page_title="Welcome",
    page_icon="📈",
    initial_sidebar_state="collapsed",
)

st.write("# Welcome to the Visual Dashboard")

st.sidebar.success("Select how to explore the data above")

st.markdown(
    """
    We investigate the changes in manufacturing and healthcare employment shares across U.S. metropolitan areas from 1980 to 2022, and how these shifts relate to demographic and economic variables.
    ### Choose your preferred way to explore the data:
    - **Guided Tour**: We curated some data that we thought readers might find interesting.
"""
)
if st.button("Enter Guided Tour"):
    st.switch_page("pages/1_Guided_Tour.py")

st.markdown(
    """
    - **Freeroam**: Explore all the data at your own pace! Choose between various indicators across metropolitan areas and states, presented with interactive maps and charts.
"""
)


if st.button("Enter Freeroam"):
    st.switch_page("pages/2_Freeroam.py")
