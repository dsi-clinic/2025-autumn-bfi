"""Homepage of Streamlit App"""

import streamlit as st

from dataprep import ensure_geojson
from gt_utilities import config

# On Streamlit Cloud (and any deploy without a pre-run Dockerfile), the GeoJSON
# is built by dataprep.py. Ensure it exists before users can open the map page.
if not config.COMBINED_GEOJSON.exists():
    ensure_geojson()

st.set_page_config(
    page_title="Welcome",
    page_icon="📈",
    initial_sidebar_state="collapsed",
)

col1, col2, col3 = st.columns([2, 5, 5])

with col2:
    if st.button("Enter Guided Tour"):
        st.switch_page("pages/1_Guided_Tour.py")
with col3:
    if st.button("Enter Free Roam"):
        st.switch_page("pages/2_Freeroam.py")

st.write(
    "<h1><em>The Rise of Healthcare Jobs</em> Data Visualization Dashboard",
    unsafe_allow_html=True,
)

st.markdown(
    "<em>The Rise of Healthcare Jobs (Gottlieb et al.)</em>: Read the working paper "
    "<a href='https://bfi.uchicago.edu/working-papers/the-rise-of-healthcare-jobs/'>"
    "here</a>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h5>Paper Abstract</h5><p>Healthcare employment has grown more than "
    "twice as fast as the labor force since 1980, overtaking retail trade to become "
    "the largest industry by employment in 2009. We document key facts about the rise "
    "of healthcare jobs. Earnings for healthcare workers have risen nearly twice as "
    "fast as those in other industries, with relatively large increases in the middle "
    "and upper-middle parts of the earnings distribution. Healthcare workers have "
    "remained predominantly female, with increases in the share of female doctors "
    "offsetting increases in the shares of male nurses and aides. Despite a few "
    "high-profile examples to the contrary, regions experiencing manufacturing job "
    "losses have not systematically reinvented themselves by pivoting from "
    "'manufacturing to meds.'",
    unsafe_allow_html=True,
)

st.markdown(
    "<h3>Purpose of Visual Dashboard</h3><p>The working paper utilizes "
    "a wealth of data pertaining to employment in healthcare, industrial manufacturing, and "
    "other sectors across 130 states and Metropolitan Statistical Areas (MSA). Exploring "
    "this data visually allows us to gain significant insight into how different regions "
    "in America are affected differently by the displacement of manufacturing-sector "
    "jobs and the subsequent rise of healthcare-sector jobs. In 2009, healthcare "
    "became the largest U.S. industry by employment, overtaking manufacturing and "
    "retail. Between 1980 and 2022, healthcare jobs have grown twice as fast as "
    "the overall labor force. The paper sought to answer the following questions:"
    "<ol><li><b>Employment Growth:</b> How and why has healthcare employment grown "
    "so rapidly relative to the rest of the U.S. labor market since 1980?</li>"
    "<li><b>Earning Trends: </b>How have healthcare wages grown, and who gained the "
    "most from that growth?</li><li><b>Demographic Change: </b>Which groups account "
    "for the rise of healthcare jobs?</li><li><b>Geographic Dynamics</b> Did places "
    "that lost manufacturing jobs replace them with healthcare jobs?",
    unsafe_allow_html=True,
)

st.markdown(
    "<h3>Choose your preferred way to explore the data:</h3>"
    "<h5><b>Guided Tour</b>: </h5>We curated data insights that we found "
    "interesting, such as trends of healthcare employment against manufacturing "
    "share, key metropolitan areas that are emerging as healthcare hubs, and what's"
    "driving this increase in healthcare employment in these areas.",
    unsafe_allow_html=True,
)

if st.button("Enter Guided Tour "):
    st.switch_page("pages/1_Guided_Tour.py")

st.markdown(
    "<h5><b>Free Roam</b>: </h5>Explore all the data at your own pace - "
    "Choose between various indicators across metropolitan areas and states, "
    "presented with interactive maps and charts.",
    unsafe_allow_html=True,
)

if st.button("Enter Free Roam "):
    st.switch_page("pages/2_Freeroam.py")
