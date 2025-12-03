"""Guided Tour - Curated Charts and Maps"""

import logging

import streamlit as st

import gt_utilities.config as config
from gt_utilities.charts import (
    make_colored_reg_chart,
    make_scatter_chart,
    plot_top_msas,
)
from gt_utilities.loaders import load_all_datasets

st.set_page_config(layout="wide")
if st.button("Go back Home"):
    st.switch_page("Homepage.py")
if st.button("Go to Freeroam"):
    st.switch_page("pages/2_Freeroam.py")
st.title("Guided Tour: Key Trends")


# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(**config.PAGE_CONFIG)

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

# Header
st.markdown(
    "<p>Over the past four decades, "
    "healthcare has quietly become one of the most important sources of employment "
    "in the United States, expanding steadily across nearly every metropolitan area"
    " regardless of economic cycles. </p><p>The data in this dashboard illustrate this "
    "transformation: some regions, such as Little Rock, Cleveland, Winston-Salem, "
    "and New Haven, now rely on healthcare for more than 12 percent of their "
    "employment, while many mid-sized metros have seen their healthcare employment"
    " shares rise by 6 to 7 percentage points since 1980. </p><p>Yet, this growth has not "
    "followed the common narrative that healthcare simply replaced manufacturing"
    " jobs; across U.S. metros, declines in manufacturing bear little relationship"
    " to how much healthcare grew. </p><p>Instead, the patterns point to deeper structural"
    " forces: population aging, the rise of chronic care, the expansion of hospital"
    " systems, and the increasing role of midlevel practitioners. Additional relationships"
    " in the data show that healthcare employment growth is only weakly related to"
    " traditional economic indicators such as earnings growth, population increases,"
    " or education levels, underscoring that healthcare’s expansion is driven more by"
    " long-run demographic demand than by short-term economic performance. </p><p>Together,"
    " these insights highlight a central finding of the underlying research: healthcare"
    " has become a stable, demographically driven anchor of local labor markets, one"
    " that grows even when other sectors shrink, and understanding its trajectory"
    " is essential for interpreting the economic future of U.S. regions.</p>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# ==============================================================
# Bar plots
# ==============================================================

st.markdown(
    "<h3>Top Metropolitan Statistical Areas (MSAs) in the Data</h3>",
    unsafe_allow_html=True,
)

# ---- Chart 1: Top MSA Healthcare Share (2022)
st.markdown(
    "<h4>Figure 1: Top 10 MSAs by Healthcare Employment Share (2022)</h4>",
    unsafe_allow_html=True,
)
st.markdown(
    "Some metropolitan areas rely much more heavily on healthcare than others. "
    "In cities like Little Rock, Cleveland, and Winston-Salem, more than 12% of all "
    "workers are now employed in healthcare. This reflects the paper’s main finding that "
    "healthcare has grown into a major and stable part of local labor markets across "
    "the country—not just in big cities, but especially in mid-sized regions with "
    "large hospital systems and medical centers."
)

try:
    bar_chart = plot_top_msas(datasets_df, "healthcare_share_prime2022")
    st.altair_chart(bar_chart, use_container_width=True)
except Exception as exc:
    st.error("Could not render the Top Healthcare Share bar chart.")
    logging.exception(exc)

st.markdown(
    "<h4>Figure 2: Top 10 MSAs by Healthcare Employment Share Change (1980-2022)</h4>",
    unsafe_allow_html=True,
)
st.markdown(
    "Since 1980, many metro areas have seen healthcare employment rise by 6 "
    "to 7 percentage points. This long-run growth highlights healthcare’s steady "
    "expansion across nearly all regions, reflecting demographic demand and the "
    "broadening of care delivery rather than short-term economic cycles."
)

# ---- Chart 2: Top MSA Healthcare Share Change Bar Chart (1980–2022)
try:
    bar_chart_2 = plot_top_msas(datasets_df, "hc_emp_share_prime_change")
    st.altair_chart(bar_chart_2, use_container_width=True)
except Exception as exc:
    st.error("Could not render the Lollipop Healthcare Growth chart.")
    logging.exception(exc)
st.markdown("<hr>", unsafe_allow_html=True)

# -------------------------
# Supplementary Charts Section
# -------------------------
st.markdown(
    "<h3>Scatterplots of Healthcare Employment Share Change Data</h3>",
    unsafe_allow_html=True,
)
fig_3_1 = make_colored_reg_chart(
    datasets_df,
    "manufacturing_share_prime1980",
    "hc_emp_share_prime_change",
    "Prime-Age Manufacturing Share (1980)",
    "Change in Prime-Age Healthcare Employment Share (1980–2022)",
    config.PALETTES[0],
    size_large=True,
)

fig_3_2 = make_colored_reg_chart(
    datasets_df,
    "change_earnings",
    "hc_emp_share_prime_change",
    "Change in Log Average Earnings (1980–2022)",
    "Change in Prime-Age Healthcare Employment Share (1980–2022)",
    config.PALETTES[0],
    size_large=True,
)

st.markdown(
    "<p class='center-caption'>This selection of scatterplots has "
    "change in healthcare employment share on their vertical axes. "
    "We can thus examine the relationships between change in healthcare "
    "employment share as a function of population, education, earnings "
    "across metropolitan areas.</p>",
    unsafe_allow_html=True,
)
st.markdown("<h5 style='text-align: center;'>Figure 3.1:</h5>", unsafe_allow_html=True)
st.altair_chart(fig_3_1, width="stretch")
st.markdown(
    "<p class='center-caption'>We first examine whether a trend of "
    "'Manufacturing-to-Meds' exists; that is, former rust-belt or cities with"
    "large industrial production capacity recasting themselves as healthcare hubs.</p>"
    "<p class='center-caption'> To avoid reverse causality and omitted variables, "
    "we predict declines in manufacturing employment using manufacturing’s share "
    "of the prime-age population in each region in 1980.</p><p>We find that "
    "the places with more baseline manufacturing only experienced modestly "
    "higher healthcare employment growth, with each 10 percentage point "
    "increase in baseline manufacturing associated with 0.7 percentage point "
    "additional growth in healthcare employment as a share of the prime-age population.</p>"
    "<p>A natural benchmark is that industries absorb manufacturing workers in "
    "proportion to their sizes. While healthcare growth counteracted roughly "
    "11% of manufacturing job losses, not much more than would be expected given "
    "its 9.8% population share, healthcare acts as a larger counteracting force "
    "for women and college-educated workers. This lends credence to the argument "
    "that high human capital levels enabled Boston to overcome its manufacturing "
    "decline. Nevertheless, a few high-profile examples of the manufacturing-to-meds "
    "pivot are outliers that do not represent a systematic trend.",
    unsafe_allow_html=True,
)

st.markdown("<h5 style='text-align: center;'>Figure 3.2:</h5>", unsafe_allow_html=True)
st.altair_chart(fig_3_2, width="stretch")
st.markdown(
    "<p class='center-caption'>Metro areas with strong wage growth did not "
    "necessarily experience faster growth in healthcare employment. "
    "This pattern suggests that healthcare expanded for reasons other than "
    "rising local incomes, growing steadily even in places with modest "
    "wage gains.</p>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h5 style='text-align: center;'>Figures 3.3-3.8<br>Scatterplots of "
    "Change in Healthcare Employment Share vs...</h5>",
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

st.markdown(
    "<p>Across U.S. metropolitan areas, changes in healthcare employment "
    "since 1980 show only weak connections to most traditional economic indicators — "
    "metro areas with faster population growth, rising wages, or higher educational "
    "attainment did not consistently experience larger healthcare sector gains, nor did "
    "regions hit hardest by manufacturing decline consistently see unusually rapid growth in healthcare.</p>"
    "<p>Instead, the only notable relationship appears to be with aging: places "
    "where the Medicare-eligible population grew more quickly (i.e. aged 65 and over)"
    "tended to see somewhat stronger increases in healthcare employment.</p>"
    "<p>At the same time, healthcare coverage expanded even in areas where labor "
    "force participation outside the sector fell, highlighting its unique stability "
    "relative to more cyclical industries. </p><p>Taken together, these patterns "
    "reflect the paper’s broader insight that the rise of healthcare jobs in America "
    "has been driven primarily by long-run demographic demand rather than short-term "
    "economic fluctuations, helping explain why healthcare has grown steadily across "
    "diverse local economies.",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# -------------------------
# GDP Relationships Section
# -------------------------
df_gdp = datasets["gdp"]

st.markdown("<h3>Scatterplots of GDP Growth Data</h3>", unsafe_allow_html=True)
st.markdown(
    "<p class='center-caption'>This selection of scatterplots has "
    "2021 GDP growth on their vertical axes. "
    "We can thus examine the relationships between economic growth "
    "and some of the key data in the BFI paper.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h5 style='text-align: center;'>Figures 4.1-4.5<br>Scatterplots of "
    "2021 GDP growth vs...</h5>",
    unsafe_allow_html=True,
)

if df_gdp is not None:
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
else:
    st.warning("GDP dataset not found. Supplementary GDP charts unavailable.")

st.markdown(
    "<p>GDP growth in 2021 is closely tied to rising population, "
    "earnings, and education levels across metros, while manufacturing continues its "
    "long-run decline. Healthcare employment, however, shows almost no relationship "
    "with GDP performance—reinforcing the paper’s insight that healthcare grows "
    "steadily regardless of short-term economic conditions.</p>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)
