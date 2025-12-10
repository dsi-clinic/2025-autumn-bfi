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
PROJECT_ROOT: Path = find_project_root()
DATA_DIR: Path = PROJECT_ROOT / "data"
BFI_SOURCE: Path = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
chart_color_scale: list[str] = config.CHART_COLOR_SCALE


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
def load_geojson(file_path: Path = config.COMBINED_GEOJSON) -> dict[str, Any]:
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
    df_selected: pd.DataFrame = df_long[df_long["indicator"] == indicator].copy()

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
    number_fmt: str = ".0%",
) -> go.Figure:
    """Generates the MapLibre choropleth figure.

    Inputs:
    - df_selected: DataFrame containing the data to plot, usually a pipeline from prepare_display_data().
    - geojson: GeoJSON dictionary for the map regions.
    - pretty_name: Pretty names mapped for display.
    - number_fmt: Formatting number presentation, following format mini-language standards
    """
    fig: go.Figure = px.choropleth_map(
        df_selected,
        geojson=geojson,
        locations="metro13",
        featureidkey="properties.region_id",
        color=pretty_name,
        color_continuous_scale=chart_color_scale,
        hover_name="metro_title",
        hover_data={pretty_name: f":{number_fmt}", "metro13": False},
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
            "tickformat": number_fmt,
        },
    )
    return fig


@st.cache_data
def generate_bar_chart(
    df_selected: pd.DataFrame, pretty_name: str, number_fmt: str = ".0%"
) -> go.Figure:
    """Generates the sorted bar chart.

    Inputs:
    - df_selected: DataFrame containing the data to plot, usually a pipeline from prepare_display_data().
    - pretty_name: The pretty name to assign to the value column for display.
    - number_fmt: Formatting number presentation, following format mini-language standards
    """
    df_bar_sorted: pd.DataFrame = df_selected.sort_values("value", ascending=False)

    fig_bar: go.Figure = px.bar(
        df_bar_sorted,
        x="metro_title",
        y=pretty_name,
        title=f"{pretty_name} by Metropolitan Area<br><i>Change drag to select/pan at top right</i>",
        color=pretty_name,
        color_continuous_scale=chart_color_scale,
        labels={"value": pretty_name, "metro_title": "Metropolitan Area"},
    )

    fig_bar.update_layout(
        coloraxis_showscale=False,
        yaxis_title="Value",
    )

    fig_bar.update_traces(
        hovertemplate=f"%{{x}}<br>Value: %{{y:{number_fmt}}}<extra></extra>"
    )

    return fig_bar


@st.cache_data
def make_scatterplot(
    datadf: pd.DataFrame,
    x_var: str,
    y_var: str,
) -> go.Figure:
    """Generates the scatterplot with Z-score coloring, custom R^2 box, and cleaner hover."""
    # Work on a copy to avoid SettingWithCopy warnings on main data
    plot_df: pd.DataFrame = datadf.copy()

    # Handle variable names safely
    pretty_x: str = config.VARIABLE_NAME_MAP.get(x_var, x_var) if x_var else ""
    pretty_y: str = config.VARIABLE_NAME_MAP.get(y_var, y_var) if y_var else ""

    # z-score for both variables for coloring
    z_x: pd.Series = (plot_df[x_var] - plot_df[x_var].min()) / plot_df[x_var].std()
    z_y: pd.Series = (plot_df[y_var] - plot_df[y_var].min()) / plot_df[y_var].std()

    # Combine them (Euclidean distance from origin in z-space)
    plot_df["z_combined"] = np.sqrt(z_x**2 + z_y**2)

    # 1. Create the Base Scatter with Trendline
    fig_scatter: go.Figure = px.scatter(
        plot_df,
        x=x_var,
        y=y_var,
        hover_name="metro_title",
        trendline="ols",
        color="z_combined",
        hover_data={"z_combined": False},
        color_continuous_scale=chart_color_scale,
        title=f"Regression: {pretty_y} vs. {pretty_x}<br><i>Drag to zoom / pan (toggle on top right)</i>",
        labels={x_var: pretty_x, y_var: pretty_y},
    )

    # 2. Extract R-squared value
    # px.get_trendline_results returns a df where the 'px_fit_results' column holds the statsmodels object
    try:
        model_results = px.get_trendline_results(fig_scatter)
        model: Any = model_results.px_fit_results.iloc[0]
        r_squared: float = model.rsquared
        slope: float = model.params[1]
        r2_text: str = f"R² = {r_squared:.3f}<br>Slope = {slope:.3f}"
    except Exception:
        r2_text = "R² = N/A"

    # 3. Add the R^2 Annotation Box
    fig_scatter.add_annotation(
        text=r2_text,
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,  # Top-left corner (adjust to 0.98, 0.98 for top-right)
        showarrow=False,
        font={"size": 14, "color": "white"},
        bgcolor="rgba(0, 0, 0, 0.4)",  # Semi-transparent black background
        bordercolor="white",
        borderwidth=1,
        borderpad=5,
        align="right",
    )

    # 4. Clean up Trendline Hover
    # Select only the trendline traces (mode='lines') and disable their hover info
    fig_scatter.update_traces(
        selector={"mode": "lines"},
        hoverinfo="skip",  # This removes the tooltip entirely from the line
        # Alternatively, use hovertemplate="%{y:.2f}" to just show values
    )

    fig_scatter.update_layout(
        title_x=0.05,
        coloraxis_showscale=False,
        xaxis={"showgrid": True, "gridcolor": "#707070"},
        yaxis={"showgrid": True, "gridcolor": "#707070"},
    )

    return fig_scatter
