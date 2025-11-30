"""Guided Tour - Curated Charts and Maps"""

import streamlit as st

import gt_utilities.config as config
from gt_utilities.charts import make_colored_reg_chart, make_scatter_chart
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
st.markdown(
    "<p style='text-align:left; color: white;'>Over the past four decades, "
    "healthcare has quietly become one of the most important sources of employment "
    "in the United States, expanding steadily across nearly every metropolitan area"
    " regardless of economic cycles. The data in this dashboard illustrate this "
    "transformation: some regions, such as Little Rock, Cleveland, Winston-Salem, "
    "and New Haven, now rely on healthcare for more than 12 percent of their "
    "employment, while many mid-sized metros have seen their healthcare employment"
    " shares rise by 6 to 7 percentage points since 1980. Yet this growth has not "
    "followed the common narrative that healthcare simply replaced manufacturing"
    " jobs; across U.S. metros, declines in manufacturing bear little relationship"
    " to how much healthcare grew. Instead, the patterns point to deeper structural"
    " forces: population aging, the rise of chronic care, the expansion of hospital"
    " systems, and the increasing role of midlevel practitioners. Additional relationships"
    " in the data show that healthcare employment growth is only weakly related to"
    " traditional economic indicators such as earnings growth, population increases,"
    " or education levels, underscoring that healthcare’s expansion is driven more by"
    " long-run demographic demand than by short-term economic performance. Together,"
    " these insights highlight a central finding of the underlying research: healthcare"
    " has become a stable, demographically driven anchor of local labor markets, one"
    " that grows even when other sectors shrink, and understanding its trajectory"
    " is essential for interpreting the economic future of U.S. regions.</p>",
    unsafe_allow_html=True,
)

# -------------------------
# Load All Datasets
# -------------------------
datasets = load_all_datasets(
    config.DATA_PATHS,
    config.MERGED_PATHS,
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
    st.altair_chart(charts[0], width="stretch")
with col2:
    st.altair_chart(charts[1], width="stretch")
with col3:
    st.altair_chart(charts[2], width="stretch")

col4, col5, col6 = st.columns(3)
with col4:
    st.altair_chart(charts[3], width="stretch")
with col5:
    st.altair_chart(charts[4], width="stretch")
with col6:
    st.altair_chart(charts[5], width="stretch")

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
        st.altair_chart(gdp_charts[0], width="stretch")
    with col2:
        st.altair_chart(gdp_charts[1], width="stretch")
    with col3:
        st.altair_chart(gdp_charts[2], width="stretch")

    # Second row: 2 charts
    col4, col5 = st.columns(2)
    with col4:
        st.altair_chart(gdp_charts[3], width="stretch")
    with col5:
        st.altair_chart(gdp_charts[4], width="stretch")

    st.markdown("<hr>", unsafe_allow_html=True)
else:
    st.warning("GDP dataset not found. Supplementary GDP charts unavailable.")
