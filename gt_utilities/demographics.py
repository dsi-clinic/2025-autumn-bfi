"""Demographics comparison module for MSA Dashboard

Handles 1980 vs 2022 population distribution analysis and visualization
"""

import pandas as pd
import streamlit as st

from gt_utilities.charts import create_demographics_comparison_chart
from gt_utilities.config import DEMOGRAPHIC_AGG_COLS, DEMOGRAPHIC_CATEGORIES


def prepare_1980_tables(min_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Prepare proportional demographics tables for 1980 data.

    Args:
        min_df: Raw population data

    Returns:
        Dictionary mapping MSA names to demographics proportion tables
    """
    msa_totals: pd.DataFrame = min_df.groupby("metro_title", as_index=False)[
        DEMOGRAPHIC_CATEGORIES
    ].sum()

    # Calculate male proportions
    male_props: pd.DataFrame = msa_totals[
        ["metro_title", "white male", "black male", "other races male", "TOT_MALE"]
    ].copy()
    male_props[["White", "Black", "Other"]] = male_props[
        ["white male", "black male", "other races male"]
    ].div(male_props["TOT_MALE"], axis=0)
    male_props = male_props[["metro_title", "White", "Black", "Other"]]

    # Calculate female proportions
    female_props: pd.DataFrame = msa_totals[
        [
            "metro_title",
            "white female",
            "black female",
            "other races female",
            "TOT_FEMALE",
        ]
    ].copy()
    female_props[["White", "Black", "Other"]] = female_props[
        ["white female", "black female", "other races female"]
    ].div(female_props["TOT_FEMALE"], axis=0)
    female_props = female_props[["metro_title", "White", "Black", "Other"]]

    # Combine into tables
    msa_tables: dict[str, pd.DataFrame] = {}
    for msa in msa_totals["metro_title"]:
        male_row: pd.Series = male_props.loc[
            male_props["metro_title"] == msa, ["White", "Black", "Other"]
        ].squeeze()
        female_row: pd.Series = female_props.loc[
            female_props["metro_title"] == msa, ["White", "Black", "Other"]
        ].squeeze()

        proportions: pd.DataFrame = pd.DataFrame(
            [male_row.to_numpy(), female_row.to_numpy()],
            index=["Male", "Female"],
            columns=["White", "Black", "Other"],
        ).astype(float)

        try:
            proportions = (proportions * 100).round(2)
            msa_tables[msa] = proportions
        except Exception as exc:
            raise ValueError(f"Error processing MSA '{msa}': {exc}") from exc

    return msa_tables


def prepare_tables(min_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Prepare proportional demographics tables for all data.

    Args:
        min_df: Raw population data

    Returns:
        Dictionary mapping MSA names to demographics proportion tables
    """
    msa_totals: pd.DataFrame = min_df.groupby("metro_title", as_index=False)[
        DEMOGRAPHIC_AGG_COLS
    ].sum()

    # Calculate male proportions
    male_props: pd.DataFrame = msa_totals[
        ["metro_title", "WAC_MALE", "BAC_MALE", "OTHER_MALE", "TOT_MALE"]
    ].copy()
    male_props[["White", "Black", "Other"]] = male_props[
        ["WAC_MALE", "BAC_MALE", "OTHER_MALE"]
    ].div(male_props["TOT_MALE"], axis=0)
    male_props = male_props[["metro_title", "White", "Black", "Other"]]

    # Calculate female proportions
    female_props: pd.DataFrame = msa_totals[
        ["metro_title", "WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE", "TOT_FEMALE"]
    ].copy()
    female_props[["White", "Black", "Other"]] = female_props[
        ["WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE"]
    ].div(female_props["TOT_FEMALE"], axis=0)
    female_props = female_props[["metro_title", "White", "Black", "Other"]]

    # Combine into tables
    msa_tables: dict[str, pd.DataFrame] = {}
    for msa in msa_totals["metro_title"]:
        male_row: pd.Series = male_props.loc[
            male_props["metro_title"] == msa, ["White", "Black", "Other"]
        ].squeeze()
        female_row: pd.Series = female_props.loc[
            female_props["metro_title"] == msa, ["White", "Black", "Other"]
        ].squeeze()

        proportions: pd.DataFrame = pd.DataFrame(
            [male_row.to_numpy(), female_row.to_numpy()],
            index=["Male", "Female"],
            columns=["White", "Black", "Other"],
        ).astype(float)

        try:
            proportions = (proportions * 100).round(2)
            msa_tables[msa] = proportions
        except Exception as exc:
            raise ValueError(f"Error processing MSA '{msa}': {exc}") from exc

    return msa_tables


def render_demographics_comparison(
    merged_pop: pd.DataFrame,
    latest_data_year: int = 2022,
    earliest_data_year: int = 1980,
    sort_states_constant: int = 2,
) -> None:
    """Render the complete demographics comparison section with interactive dropdown.

    Args:
        merged_pop: Merged population DataFrame containing both year's data
        latest_data_year: The later year with data (default: 2022)
        earliest_data_year: The earliest year with data (default: 1980)
        sort_states_constant: Length of state name, used for filtering out
            states from this chart since they have no data
    """
    # Prepare tables
    merged_pop["year"] = pd.to_numeric(merged_pop["year"], errors="coerce")

    merged_pop_2022: pd.DataFrame = merged_pop[merged_pop["year"] == latest_data_year]
    merged_pop_1980: pd.DataFrame = merged_pop[merged_pop["year"] == earliest_data_year]
    msa_tables_2022: dict[str, pd.DataFrame] = prepare_tables(merged_pop_2022)
    msa_tables_1980: dict[str, pd.DataFrame] = prepare_1980_tables(merged_pop_1980)

    # Get common MSAs and filter out states since states have no demographics data
    common_msas: list[str] = [
        msa
        for msa in sorted(set(msa_tables_1980.keys()) & set(msa_tables_2022.keys()))
        if len(msa) > sort_states_constant
    ]

    if not common_msas:
        st.warning("No common MSAs found between 1980 and 2022 datasets.")
        return

    # Section header
    st.header("Population Distribution by Race and Sex (1980 vs 2022)")
    st.markdown(
        "<p class='center-caption'>Compare Male/Female racial shares side-by-side for the selected MSA.</p>",
        unsafe_allow_html=True,
    )

    # Dropdown selection
    selected_msa: str = st.selectbox(
        "Select a Metropolitan Statistical Area (MSA):", common_msas, index=0
    )

    # Side-by-side tables
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### {selected_msa} — 1980", unsafe_allow_html=True)
        st.dataframe(msa_tables_1980[selected_msa])

    with col2:
        st.markdown(f"#### {selected_msa} — 2022", unsafe_allow_html=True)
        st.dataframe(msa_tables_2022[selected_msa])

    # Comparison chart
    bar_chart = create_demographics_comparison_chart(
        msa_tables_1980[selected_msa], msa_tables_2022[selected_msa], selected_msa
    )
    st.altair_chart(bar_chart, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
