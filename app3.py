"""Web app to visualize MSA/state-level data on a MapLibre map using Plotly and Streamlit."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# from streamlit_plotly_events import plotly_events

# --- Load data ---
datadf = pd.read_csv("data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv")


@st.cache_data
def melt_dataframe(datadf: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Convert wide dataframe to long format for easier plotting. Cached for faster performance.

    datadf: Original wide dataframe.
    """
    value_cols = [c for c in datadf.columns if c not in ["metro13", "metro_title"]]
    df_long = datadf.melt(
        id_vars=["metro13", "metro_title"],
        value_vars=value_cols,
        var_name="indicator",
        value_name="value",
    )
    return df_long, value_cols


df_long, value_cols = melt_dataframe(datadf)


@st.cache_data
def load_geojson(file_path: str = "data/combined_US_regions.geojson") -> dict:
    """Load combined GeoJSON for US regions. Cached for faster performance.

    file_path: Path to geojson file.
    """
    with Path.open(file_path) as f:
        return json.load(f)


combined_geo = load_geojson()

# --- Streamlit setup ---
st.set_page_config(layout="wide")
st.title("Metropolitan Area and Statewide Healthcare Data Explorer")
indicator = st.selectbox(
    "Select variable to visualize:", df_long["indicator"].unique(), key="main_indicator"
)
df_sel = df_long[df_long["indicator"] == indicator].copy()
df_sel["metro13"] = df_sel["metro13"].astype(str)

# --- Session state for clicked MSAs ---
if "selected_metros" not in st.session_state:
    st.session_state.selected_metros = []

# --- Base map figure (static opacity) ---
color_min = df_sel["value"].min()
color_max = df_sel["value"].max()

# --- Create the MapLibre choropleth
fig = px.choropleth_map(
    df_sel,
    geojson=combined_geo,
    locations="metro13",
    featureidkey="properties.region_id",  # adjust to your geojson property
    color="value",
    color_continuous_scale="viridis",
    hover_name="metro_title",
    hover_data={"value": True, "metro13": False},
    map_style="open-street-map",  # built-in style under MapLibre
    zoom=3,
    center={"lat": 37.8, "lon": -96},
    opacity=0.75,
    labels={"value": indicator},
)

fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=800)

st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

# --- Filter bar chart by selected MSAs ---
if st.session_state.selected_metros:
    df_bar_sorted = df_sel[
        df_sel["metro13"].isin(st.session_state.selected_metros)
    ].sort_values("value", ascending=False)
else:
    df_bar_sorted = df_sel.sort_values("value", ascending=False)

fig_bar = px.bar(
    df_bar_sorted,
    x="metro_title",
    y="value",
    color="value",
    color_continuous_scale="viridis",
    labels={"value": indicator, "metro_title": "Metro Area"},
)

st.plotly_chart(fig_bar, use_container_width=True)

# --- Create user-generated scatterplot for selected variables ---
st.header("Explore Relationships Between Variables")
st.markdown("### Visualize correlations between any two indicators below.")

y_var = st.selectbox("Select Response (y) variable", [""] + value_cols)
x_var = st.selectbox("Select Explanatory (x) variable", [""] + value_cols)


# Only create the scatterplot if both variables are selected
if x_var and y_var:
    fig_scatter = px.scatter(
        datadf,
        x=x_var,
        y=y_var,
        hover_name="metro_title",
        trendline="ols",
        # color="metro_title",  # or choose a numeric column, or remove this line
        title=f"Regression: {y_var} vs. {x_var}",
        labels={x_var: x_var, y_var: y_var},
    )

    fig_scatter.update_layout(
        plot_bgcolor="#555555",  # the plotting area
        paper_bgcolor="#555555",  # the surrounding area
    )

    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Select two variables above to view a regression scatterplot.")
