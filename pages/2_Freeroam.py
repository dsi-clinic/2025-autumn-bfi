"""Web app to visualize MSA/state-level data on a MapLibre map using Plotly and Streamlit."""

import json
from pathlib import Path

import numpy as np
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
def get_variable_name_map() -> dict[str, str]:
    """Get mapping of variable codes to human-readable names."""
    return {
        "ln_msa_pop1980": "Log Population (1980)",
        "ln_msa_pop2022": "Log Population (2022)",
        "change_ln_population": "Change in Log Population (1980–2022)",
        "change_ln_non_hc": "Change in Log Non-Healthcare Employment (1980–2022)",
        "change_non_hc_share_lbfr": "Change in Non-Healthcare Labor Force Share (1980–2022)",
        "healthcare_share_prime1980": "Prime-Age Healthcare Share (1980)",
        "healthcare_share_prime2022": "Prime-Age Healthcare Share (2022)",
        "hc_emp_share_prime_change": "Change in Prime-Age Healthcare Employment Share (1980–2022)",
        "manufacturing_share_prime1980": "Prime-Age Manufacturing Share (1980)",
        "manu_share_prime_change": "Change in Prime-Age Manufacturing Share (1980–2022)",
        "non_hc_share_prime_change": "Change in Non-Healthcare Prime-Age Employment Share (1980–2022)",
        "not_lbfr_share_prime_change": "Change in Prime-Age Not-in-Labor-Force Share (1980–2022)",
        "unemployed_share_prime_change": "Change in Prime-Age Unemployment Share (1980–2022)",
        "non_hc_manu_share_prime_change": "Change in Prime-Age Non-HC & Non-Manufacturing Employment Share (1980–2022)",
        "non_manu_share_prime_change": "Change in Prime-Age Non-Manufacturing Share (1980–2022)",
        "medicare_share1980": "Medicare Share (1980)",
        "medicare_share2022": "Medicare Share (2022)",
        "change_medicare_share": "Change in Medicare Share (1980–2022)",
        "ln_aearn1980": "Log Average Earnings (1980)",
        "ln_aearn2022": "Log Average Earnings (2022)",
        "change_earnings": "Change in Log Average Earnings (1980–2022)",
        "college1980": "College Degree Share (1980)",
        "college2022": "College Degree Share (2022)",
        "change_college": "Change in College Degree Share (1980–2022)",
    }


variable_name_map = get_variable_name_map()


@st.cache_data
def load_geojson(file_path: str = "data/combined_US_regions_auto.geojson") -> dict:
    """Load combined GeoJSON for US regions. Cached for faster performance.

    file_path: Path to geojson file. Default is 'data/combined_US_regions_auto.geojson', generated from dataprep.py.
    """
    with Path.open(file_path) as f:
        return json.load(f)


combined_geo = load_geojson()

# --- Streamlit setup ---
st.set_page_config(layout="wide")
if st.button("Go back Home"):
    st.switch_page("Homepage.py")

if st.button("Go to Guided Tour"):
    st.switch_page("pages/1_Guided_Tour.py")
st.title("Metropolitan Area and Statewide Healthcare Data Explorer")
indicator = st.selectbox(
    "Select variable",
    options=value_cols,
    format_func=lambda x: variable_name_map.get(x, x),
)
pretty = variable_name_map.get(
    indicator, indicator
)  # Beautifies variable name for display
df_sel = df_long[df_long["indicator"] == indicator].copy()
df_sel["metro13"] = df_sel["metro13"].astype(str)  # ensure string type for matching
df_sel[pretty] = df_sel["value"]

# # --- Session state for clicked MSAs ---
# if "selected_metros" not in st.session_state:
#     st.session_state.selected_metros = []

# --- Base map figure (static opacity) ---
color_min = df_sel["value"].min()
color_max = df_sel["value"].max()

# --- Create the MapLibre choropleth
fig_map = px.choropleth_map(
    df_sel,
    geojson=combined_geo,
    locations="metro13",
    featureidkey="properties.region_id",  # adjust to your geojson property
    color=pretty,
    color_continuous_scale="orrd",
    hover_name="metro_title",
    hover_data={pretty: ":.2f", "metro13": False},
    map_style="open-street-map",  # built-in style under MapLibre
    zoom=3,
    center={"lat": 37.8, "lon": -96},
    opacity=0.75,
)

fig_map.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    height=800,
    coloraxis_colorbar={
        "orientation": "h",
        "yanchor": "top",
        "y": 0.15,
        "xanchor": "center",
        "x": 0.5,
        "len": 0.6,
        "bgcolor": "rgba(10, 10, 10, 0.85)",
        "thickness": 15,
        "title": pretty,
        "title_side": "top",
    },
)

st.plotly_chart(fig_map, use_container_width=True, config={"scrollZoom": True})

# --- Filter bar chart by selected MSAs ---
df_bar_sorted = df_sel.sort_values("value", ascending=False)

fig_bar = px.bar(
    df_bar_sorted,
    x="metro_title",
    y=pretty,
    title=f"{pretty} by Metropolitan Area<br><i>Drag to select</i>",
    color=pretty,
    color_continuous_scale="orrd",
    labels={"value": pretty, "metro_title": "Metropolitan Area"},
)
fig_bar.update_layout(
    coloraxis_showscale=False,
    yaxis_title="Value",
)

fig_bar.update_traces(hovertemplate="%{x}<br>Value: %{y:.2f}<extra></extra>")

st.plotly_chart(fig_bar, use_container_width=True)

# --- Create user-generated scatterplot for selected variables ---
st.header("Explore Relationships Between Variables")
st.markdown("### Visualize correlations between any two indicators below.")

y_var = st.selectbox(
    "Select Response (y) variable",
    options=[""] + value_cols,
    format_func=lambda x: variable_name_map.get(x, x),
)
x_var = st.selectbox(
    "Select Explanatory (x) variable",
    options=[""] + value_cols,
    format_func=lambda x: variable_name_map.get(x, x),
)

pretty_x = variable_name_map.get(x_var, x_var) if x_var else ""
pretty_y = variable_name_map.get(y_var, y_var) if y_var else ""

# Only create the scatterplot if both variables are selected
if x_var and y_var:
    z_x = (datadf[x_var] - datadf[x_var].min()) / datadf[x_var].std()
    z_y = (datadf[y_var] - datadf[y_var].min()) / datadf[y_var].std()

    # Combine them (e.g., Euclidean distance from origin in z-space)
    datadf["z_combined"] = np.sqrt(z_x**2 + z_y**2)

    fig_scatter = px.scatter(
        datadf,
        x=x_var,
        y=y_var,
        hover_name="metro_title",
        trendline="ols",
        color="z_combined",
        hover_data={"z_combined": False},
        color_continuous_scale="orrd",
        title=f"Regression: {pretty_y} vs. {pretty_x}<br><i>Drag to zoom</i>",
        labels={x_var: pretty_x, y_var: pretty_y},
    )

    fig_scatter.update_layout(
        title_x=0.05,
        plot_bgcolor="#606060",  # the plotting area
        paper_bgcolor="#656565",  # the surrounding area
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Select two variables above to view a regression scatterplot.")
