"""Web app to visualize MSA/state-level data on a MapLibre map using Plotly and Streamlit."""

import pandas as pd
import streamlit as st

import gt_utilities.map_visualization_helper as map_utils
from gt_utilities import config
from gt_utilities.demographics import render_demographics_comparison
from gt_utilities.loaders import load_all_datasets

# --- Load data ---
DATA_DIR = config.DATA_DIR
VARIABLE_NAME_MAP: dict[str, str] = config.VARIABLE_NAME_MAP

datadf: pd.DataFrame = pd.read_csv(config.DATA_PATHS)
df_long_for_display, value_columns = map_utils.melt_dataframe(datadf)
combined_geo = map_utils.load_geojson()

# --- Streamlit setup ---
st.set_page_config(layout="wide")
if st.button("Go back Home"):
    st.switch_page("Homepage.py")

if st.button("Go to Guided Tour"):
    st.switch_page("pages/1_Guided_Tour.py")
st.title("Free Roam: Metropolitan Area and Statewide Healthcare Data Explorer")

st.markdown(
    "<p>This page displays all our data in an interactive format, "
    "allowing you to browse at your own pace. </p>",
    unsafe_allow_html=True,
)

indicator = st.selectbox(
    "Select variable for map and bar plot",
    options=value_columns,
    format_func=lambda x: VARIABLE_NAME_MAP.get(x, x),
)

st.markdown(
    "<p><em>“Prime-age” is defined as individuals 25-54 years old</em></p>"
    "<p><em>Changes in logarithmic figures ('Log') is equivalent "
    "to percentage increase (positive log) / decrease (negative log) divided "
    "by 100</em></p>",
    unsafe_allow_html=True,
)

pretty: str = VARIABLE_NAME_MAP.get(indicator, indicator)

df_selected_variables = map_utils.prepare_display_data(
    df_long_for_display, indicator, pretty
)

# -------------------------
# Create the MapLibre choropleth
# -------------------------
fig_map = map_utils.generate_choropleth_map(df_selected_variables, combined_geo, pretty)

st.plotly_chart(fig_map, width="stretch", config={"scrollZoom": True})

# -------------------------
# Create complementary bar chart to the choropleth
# -------------------------
fig_bar = map_utils.generate_bar_chart(
    df_selected_variables,
    pretty,
)

st.plotly_chart(fig_bar, width="stretch")

# -------------------------
# Create user-generated scatterplot for selected variables
# -------------------------
st.header("Create your own scatterplot")

y_var = st.selectbox(
    "Select Response (y) variable",
    options=[""] + value_columns,
    format_func=lambda x: VARIABLE_NAME_MAP.get(x, x),
)
x_var = st.selectbox(
    "Select Explanatory (x) variable",
    options=[""] + value_columns,
    format_func=lambda x: VARIABLE_NAME_MAP.get(x, x),
)
# Only create the scatterplot if both variables are selected
if x_var and y_var:
    fig_scatter = map_utils.make_scatterplot(
        datadf,
        x_var,
        y_var,
    )
    st.plotly_chart(fig_scatter, width="stretch")
else:
    st.info("Select two variables above to view a regression scatterplot.")

# -------------------------
# Demographics Comparison Section
# -------------------------

datasets = load_all_datasets(
    config.DATA_PATHS,
    config.MERGED_PATHS,
    config.GDP_PATHS,
)

merged_pop = datasets["merged"]

if merged_pop is not None:
    render_demographics_comparison(merged_pop)
else:
    st.warning(
        "1980/2022 population detail files not found. Skipping the demographics comparison section. "
        "Place files in Downloads or ../data and reload."
    )
