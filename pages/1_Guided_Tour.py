"""Guided Tour - Curated Charts and Maps"""

import streamlit as st

import gt_utilities.config as config
from gt_utilities.charts import make_colored_reg_chart, make_scatter_chart
from gt_utilities.demographics import render_demographics_comparison
from gt_utilities.loaders import load_all_datasets

st.set_page_config(layout="wide")
if st.button("Go back Home"):
    st.switch_page("Homepage.py")

if st.button("Go to Freeroam"):
    st.switch_page("pages/2_Freeroam.py")
st.title("Interactive Maps of MSA's")


# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(**config.PAGE_CONFIG)

# -------------------------
# Apply Custom Styling
# -------------------------
st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------
# Header Section
# -------------------------
st.markdown("<h1>Interactive Maps of MSA's</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color: white;'>Understanding the socioeconomic and demographic factors behind healthcare employment growth across U.S. MSAs (1980–2022).</p>",
    unsafe_allow_html=True,
)

# -------------------------
# Load All Datasets
# -------------------------
datasets = load_all_datasets(
    config.DATA_PATHS,
    config.CLEANED_PATHS,
    config.MERGED_1980_PATHS,
    config.MIN_2022_PATHS,
    config.GDP_PATHS,
)

# Stop if main dataset is missing
if datasets["main"] is None:
    st.stop()

datasets_df = datasets["main"]

# -------------------------
# Supplementary Charts Section
# -------------------------
st.markdown("<h3>Supplementary Charts</h3>", unsafe_allow_html=True)
st.markdown(
    "<p class='center-caption'>These supplementary charts provide additional context for understanding relationships between population, education, earnings, and healthcare employment growth across MSAs.</p>",
    unsafe_allow_html=True,
)

# Build individual charts
charts = [make_colored_reg_chart(datasets_df, *r) for r in config.RELATIONSHIPS]

# Render in a 2x3 grid
col1, col2, col3 = st.columns(3)
with col1:
    st.altair_chart(charts[0], use_container_width=True)
with col2:
    st.altair_chart(charts[1], use_container_width=True)
with col3:
    st.altair_chart(charts[2], use_container_width=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.altair_chart(charts[3], use_container_width=True)
with col5:
    st.altair_chart(charts[4], use_container_width=True)
with col6:
    st.altair_chart(charts[5], use_container_width=True)

# -------------------------
# GDP Relationships Section
# -------------------------
df_gdp = datasets["gdp"]

if df_gdp is not None:
    st.markdown("<h3>GDP Growth Relationships (2021)</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p class='center-caption'>Explore how GDP growth in 2021 relates to key economic indicators across MSAs.</p>",
        unsafe_allow_html=True,
    )

    # Build GDP charts
    gdp_charts = [make_scatter_chart(df_gdp, *r) for r in config.GDP_RELATIONSHIPS]

    # First row: 3 charts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.altair_chart(gdp_charts[0], use_container_width=True)
    with col2:
        st.altair_chart(gdp_charts[1], use_container_width=True)
    with col3:
        st.altair_chart(gdp_charts[2], use_container_width=True)

    # Second row: 2 charts
    col4, col5 = st.columns(2)
    with col4:
        st.altair_chart(gdp_charts[3], use_container_width=True)
    with col5:
        st.altair_chart(gdp_charts[4], use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
else:
    st.warning("GDP dataset not found. Supplementary GDP charts unavailable.")

# -------------------------
# Demographics Comparison Section
# -------------------------
merged_pop_1980 = datasets["merged_1980"]
min_df_2022 = datasets["min_2022"]

if merged_pop_1980 is None or min_df_2022 is None:
    st.warning(
        "1980/2022 population detail files not found. Skipping the demographics comparison section. "
        "Place files in Downloads or ../data and reload."
    )
else:
    render_demographics_comparison(merged_pop_1980, min_df_2022)
