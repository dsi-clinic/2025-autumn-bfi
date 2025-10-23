"""Web app to visualize MSA/state-level data on a MapLibre map using Plotly and Streamlit."""

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

# --- Load environment variables (if using .env) ---
load_dotenv()
# You may not *need* a token for built-in styles, but if you use a custom style, you might.
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

# --- Load your data ---
# For example:
# df_long: columns ⇒ metro13, metro_title, indicator, value
datadf = pd.read_csv(
    "data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
)  # replace
value_cols = [c for c in datadf.columns if c not in ["metro13", "metro_title"]]
df_long = datadf.melt(
    id_vars=["metro13", "metro_title"],
    value_vars=value_cols,
    var_name="indicator",
    value_name="value",
)

# --- Load your GeoJSON boundaries (MSAs)
with Path.open("data/2021_US_CBSA.geojson") as f:
    msa_geo = json.load(f)

# --- Streamlit UI: dropdown for indicator
st.title("MSA / State Data Explorer")
indicator = st.selectbox("Select variable:", value_cols)

df_sel = df_long[df_long["indicator"] == indicator].copy()
df_sel["metro13"] = df_sel["metro13"].astype(str)  # ensure string for matching

# --- Create the MapLibre choropleth
fig = px.choropleth_map(
    df_sel,
    geojson=msa_geo,
    locations="metro13",
    featureidkey="properties.CBSAFP",  # adjust to your geojson property
    color="value",
    color_continuous_scale="viridis",
    hover_name="metro_title",
    hover_data={"value": True, "metro13": False},
    map_style="open-street-map",  # built-in style under MapLibre
    zoom=3,
    center={"lat": 37.8, "lon": -96},
    opacity=0.7,
    labels={"value": indicator},
)

fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})

# --- Display in Streamlit
st.plotly_chart(fig, use_container_width=True)
