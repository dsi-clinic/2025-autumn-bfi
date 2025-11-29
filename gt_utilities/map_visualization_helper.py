"""Helper for app to visualize MSA/state-level data on a MapLibre map using Plotly and Streamlit."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from gt_utilities import config, find_project_root

# --- Load data ---
PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data"
BFI_SOURCE = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"


@st.cache_data
def melt_dataframe(datadf: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Convert wide dataframe to long format for easier plotting. Cached for faster performance.

    datadf: Original wide dataframe.
    """
    value_cols: list[str] = [
        c for c in datadf.columns if c not in ["metro13", "metro_title"]
    ]
    df_long: pd.DataFrame = datadf.melt(
        id_vars=["metro13", "metro_title"],
        value_vars=value_cols,
        var_name="indicator",
        value_name="value",
    )
    return df_long, value_cols


@st.cache_data
def load_geojson(file_path: Path = config.COMBINED_GEOJSON) -> dict:
    """Load combined GeoJSON for US regions. Cached for faster performance.

    file_path: Path to geojson file. Default is 'data/combined_US_regions_auto.geojson', generated from dataprep.py.
    """
    with Path.open(file_path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def prepare_display_data(
    df_long: pd.DataFrame, indicator: str, pretty_name: str
) -> pd.DataFrame:
    """Filters the long dataframe for the selected indicator and renames the value column for pretty display in tooltips.

    Inputs:
    - df_long: DataFrame in long format with 'indicator' and 'value' columns.
    - indicator: The specific indicator to filter for.
    - pretty_name: The pretty name to assign to the value column for display.
    """
    # Filter for the specific indicator
    df_selected = df_long[df_long["indicator"] == indicator].copy()

    # Ensure string type for matching GeoJSON
    df_selected["metro13"] = df_selected["metro13"].astype(str)

    # Create the column with the "Pretty Name" so tooltips look nice
    df_selected[pretty_name] = df_selected["value"]

    return df_selected


@st.cache_data(show_spinner=False)
def generate_choropleth_map(
    df_selected: pd.DataFrame,
    geojson: dict[str, Any],
    pretty_name: str,
) -> go.Figure:
    """Generates the MapLibre choropleth figure.

    Inputs:
    - df_selected: DataFrame containing the data to plot, usually a pipeline from prepare_display_data().
    - geojson: GeoJSON dictionary for the map regions.
    - pretty_name: Pretty names mapped for display.
    """
    fig = px.choropleth_map(
        df_selected,
        geojson=geojson,
        locations="metro13",
        featureidkey="properties.region_id",
        color=pretty_name,
        color_continuous_scale="orrd",
        hover_name="metro_title",
        hover_data={pretty_name: ":.2f", "metro13": False},
        map_style="open-street-map",
        zoom=3,
        center={"lat": 37.8, "lon": -96},
        opacity=0.75,
    )

    fig.update_layout(
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
            "title": pretty_name,
            "title_side": "top",
        },
    )
    return fig


@st.cache_data
def generate_bar_chart(df_selected: pd.DataFrame, pretty_name: str) -> go.Figure:
    """Generates the sorted bar chart.

    Inputs:
    - df_selected: DataFrame containing the data to plot, usually a pipeline from prepare_display_data().
    - pretty_name: The pretty name to assign to the value column for display.
    """
    df_bar_sorted = df_selected.sort_values("value", ascending=False)

    fig_bar = px.bar(
        df_bar_sorted,
        x="metro_title",
        y=pretty_name,
        title=f"{pretty_name} by Metropolitan Area<br><i>Drag to select</i>",
        color=pretty_name,
        color_continuous_scale="orrd",
        labels={"value": pretty_name, "metro_title": "Metropolitan Area"},
    )

    fig_bar.update_layout(
        coloraxis_showscale=False,
        yaxis_title="Value",
    )

    fig_bar.update_traces(hovertemplate="%{x}<br>Value: %{y:.2f}<extra></extra>")

    return fig_bar


@st.cache_data
def make_scatterplot(
    datadf: pd.DataFrame,
    x_var: str,
    y_var: str,
) -> go.Figure:
    """Generates the scatterplot with Z-score coloring."""
    # Work on a copy to avoid SettingWithCopy warnings on main data
    plot_df = datadf.copy()

    pretty_x = config.VARIABLE_NAME_MAP.get(x_var, x_var) if x_var else ""
    pretty_y = config.VARIABLE_NAME_MAP.get(y_var, y_var) if y_var else ""

    # z-score for both variables for coloring
    z_x = (plot_df[x_var] - plot_df[x_var].min()) / plot_df[x_var].std()
    z_y = (plot_df[y_var] - plot_df[y_var].min()) / plot_df[y_var].std()

    # Combine them (Euclidean distance from origin in z-space)
    plot_df["z_combined"] = np.sqrt(z_x**2 + z_y**2)

    fig_scatter = px.scatter(
        plot_df,
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

    return fig_scatter
