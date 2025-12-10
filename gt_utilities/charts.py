"""Chart construction utilities for MSA Dashboard

Centralizes all Altair chart creation and styling
"""

import logging

import altair as alt
import pandas as pd
from sklearn.linear_model import LinearRegression

from gt_utilities import setup_logger
from gt_utilities.config import CHART_COLOR_SCALE, VARIABLE_NAME_MAP

LOGGER: logging.Logger = setup_logger(__name__)
alt.data_transformers.disable_max_rows()


def compute_regression_stats(
    datadf: pd.DataFrame, predictor_column: str, response_column: str
) -> str:
    """Compute and format regression statistics.

    Args:
        datadf: DataFrame containing the data to be analyzed
        predictor_column: Column name for x-axis variable, the predictor variable
        response_column: Column name for y-axis variable, the predicted/response variable

    Returns:
        Formatted string with slope and R² values
    """
    try:
        model: LinearRegression = LinearRegression()
        x_vals: pd.DataFrame = datadf[[predictor_column]].dropna()
        y_vals: pd.Series = datadf[response_column].dropna()

        # Align indices
        y_aligned: pd.Series = y_vals.loc[x_vals.index]

        if len(x_vals) == 0 or len(y_aligned) == 0:
            return "Regression unavailable"

        model.fit(x_vals, y_aligned)
        r2: float = model.score(x_vals, y_aligned)
        slope: float = model.coef_[0]

        return f"Slope={slope:.2f}, R²={r2:.2f}"
    except Exception as e:
        LOGGER.warning(
            f"Could not compute regression stats for {predictor_column} vs {response_column}: {e}"
        )
        return "Regression unavailable"


def make_colored_reg_chart(
    datadf: pd.DataFrame,
    predictor_column: str,
    response_column: str,
    predictor_label: str,
    response_label: str,
    palette: list[str],
    size_large: bool = False,
) -> alt.Chart | str:
    """Create an Altair scatterplot with regression line and tooltip + stats.

    Args:
        datadf: DataFrame containing the data to be visualized
        predictor_column: Column name for predictor variable
        response_column: Column name for response variable
        predictor_label: Display label for predictor variable
        response_label: Display label for response variable
        palette: List of colors [scatter_color, line_color, ...]
        size_large: Whether to display a fullsize chart.

    Returns:
        Configured Altair chart
    """
    try:
        LOGGER.info(f"Building chart: {response_label} vs {predictor_label}")

        base: alt.Chart = alt.Chart(datadf).encode(
            x=alt.X(
                predictor_column,
                title=predictor_label,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12),
            ),
            y=alt.Y(
                response_column,
                title=response_label,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12),
            ),
        )

        points: alt.Chart = base.mark_circle(
            size=80, opacity=0.75, color=palette[0]
        ).encode(
            tooltip=[
                alt.Tooltip("metro_title:N", title="MSA"),
                alt.Tooltip(predictor_column, title=predictor_label, format=".2%"),
                alt.Tooltip(response_column, title=response_label, format=".2%"),
            ]
        )

        # Regression line (Altair transform_regression)
        regression: alt.Chart = base.transform_regression(
            predictor_column, response_column, method="linear"
        ).mark_line(color=palette[1], size=2.5)

        # Regression stats text
        stats_label: str = compute_regression_stats(
            datadf, predictor_column, response_column
        )
        stats_text: alt.Chart = (
            alt.Chart(pd.DataFrame({"text": [stats_label]}))
            .mark_text(align="left", x=10, y=15, fontSize=10, color="black")
            .encode(text="text:N")
        )

        if size_large:
            chart: alt.Chart = (points + regression + stats_text).properties(
                width=340, height=530, title=f"{response_label} vs. {predictor_label}"
            )
        else:
            chart: alt.Chart = (points + regression + stats_text).properties(
                width=340, height=330, title=predictor_label
            )

        return chart
    except Exception as e:
        LOGGER.warning(f"Could not create altair scatterplot: {e}")
        return "scatterplot unavailable"


def make_scatter_chart(
    datadf: pd.DataFrame,
    predictor_variable: str,
    response_variable: str,
    predictor_label: str,
    response_label: str,
    color: str,
) -> alt.Chart | str:
    """Create a scatter plot with regression line (simplified for GDP charts).

    Args:
        datadf: DataFrame containing the data
        predictor_variable: Column name for predictor variable
        response_variable: Column name for response variable
        predictor_label: Display label for predictor variable
        response_label: Display label for response variable
        color: Color for scatter points

    Returns:
        Configured Altair chart
    """
    try:
        base: alt.Chart = alt.Chart(datadf).encode(
            x=alt.X(
                predictor_variable,
                title=predictor_label,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12),
            ),
            y=alt.Y(
                response_variable,
                title=response_label,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12),
            ),
        )

        scatter: alt.Chart = base.mark_circle(size=80, opacity=0.7, color=color).encode(
            tooltip=[
                alt.Tooltip("metro_title:N", title="MSA"),
                alt.Tooltip(predictor_variable, title=predictor_label, format=".2f"),
                alt.Tooltip(response_variable, title=response_label, format=".2f"),
            ]
        )

        regression: alt.Chart = base.transform_regression(
            predictor_variable, response_variable
        ).mark_line(color=color, strokeWidth=2)

        return (scatter + regression).properties(
            width=330, height=400, title=predictor_label
        )
    except Exception as e:
        LOGGER.warning(f"Could not create altair scatterplot: {e}")
        return "scatterplot unavailable"


def create_demographics_comparison_chart(
    df_1980: pd.DataFrame, df_2022: pd.DataFrame, msa_name: str
) -> alt.Chart | str:
    """Create a grouped bar chart comparing demographics between 1980 and 2022.

    Args:
        df_1980: 1980 demographics table for the MSA
        df_2022: 2022 demographics table for the MSA
        msa_name: Name of the MSA (for display)

    Returns:
        Configured Altair grouped bar chart
    """
    try:
        # Prepare data
        chart_df_1980: pd.DataFrame = df_1980.reset_index().melt(
            id_vars="index", var_name="Race", value_name="Percentage"
        )
        chart_df_1980["Year"] = "1980"

        chart_df_2022: pd.DataFrame = df_2022.reset_index().melt(
            id_vars="index", var_name="Race", value_name="Percentage"
        )
        chart_df_2022["Year"] = "2022"

        combined_df: pd.DataFrame = pd.concat([chart_df_1980, chart_df_2022]).rename(
            columns={"index": "Gender"}
        )

        # Keep only White and Black for clarity
        combined_df = combined_df[combined_df["Race"].isin(["White", "Black"])]
        combined_df["Group"] = combined_df["Gender"] + " (" + combined_df["Year"] + ")"

        # Create chart
        bar_chart: alt.Chart = (
            alt.Chart(combined_df)
            .mark_bar(size=28)
            .encode(
                x=alt.X("Group:N", title=None, axis=alt.Axis(labelFontSize=12)),
                y=alt.Y("Percentage:Q", title="Percentage"),
                color=alt.Color(
                    "Race:N",
                    scale=alt.Scale(range=["#ecd2c2", "#800000"]),
                    legend=alt.Legend(title="Race"),
                ),
                tooltip=["Gender", "Year", "Race", "Percentage"],
            )
            .properties(width=480, height=320)
            .configure_view(strokeWidth=0)
        )

        return bar_chart
    except Exception as e:
        LOGGER.warning(f"Could not create altair grouped bar chart: {e}")
        return "grouped bar chart unavailable"


# ------------------------------------------------------
# Bar Chart: Top MSAs by Healthcare Employment Share
# ------------------------------------------------------


def plot_top_msas(df: pd.DataFrame, variable: str, top_n: int = 10) -> alt.Chart | str:
    """Create a bar chart of the top N MSAs ranked by the specified variable.

    Args:
        df (pd.DataFrame): Source DataFrame.
        variable (str): Column name to rank MSAs by.
        top_n (int, optional): Number of MSAs to include. Defaults to 10.

    Returns:
        alt.Chart or str: Altair bar chart or a fallback message if chart creation fails.
    """
    try:
        top_df: pd.DataFrame = df.nlargest(top_n, variable).copy()
        pretty: str = VARIABLE_NAME_MAP.get(variable, variable)

        chart: alt.Chart = (
            alt.Chart(top_df)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                y=alt.Y(
                    "metro_title:N",
                    sort="-x",
                    axis=alt.Axis(labelFontSize=13, labelLimit=350, title=None),
                ),
                x=alt.X(
                    variable,
                    title=pretty,
                    axis=alt.Axis(
                        format=".0%",
                        labelFontSize=12,
                        titleFontSize=14,
                        grid=False,
                        tickMinStep=0.01,
                    ),
                ),
                color=alt.Color(
                    variable,
                    scale=alt.Scale(range=CHART_COLOR_SCALE),
                    legend=None,
                ),
                tooltip=[
                    "metro_title",
                    alt.Tooltip(variable, format=".2%"),
                ],
            )
            .properties(
                width=700,
                height=450,
            )
            .configure_title(fontSize=18, font="Lato", anchor="start")
            .configure_axis(labelFont="Lato", titleFont="Lato", grid=False)
            .configure_view(strokeWidth=0)
        )

        LOGGER.info(f"Generated bar chart for top {top_n} MSAs.")
        return chart
    except Exception as e:
        LOGGER.warning(f"Could not create bar chart for '{variable}': {e}")
        return "bar chart unavailable"
