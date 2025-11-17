"""
Demographics comparison module for MSA Dashboard
Handles 1980 vs 2022 population distribution analysis and visualization
"""
from typing import Dict

import pandas as pd
import streamlit as st

from config import DEMOGRAPHIC_CATEGORIES, DEMOGRAPHIC_AGG_COLS
from charts import create_demographics_comparison_chart


def prepare_1980_tables(merged_pop_1980: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Prepare proportional demographics tables for 1980 data.
    
    Args:
        merged_pop_1980: Raw 1980 population data
    
    Returns:
        Dictionary mapping MSA names to demographics proportion tables
    """
    agg = merged_pop_1980.groupby(
        ["metro_title", "Race/Sex Indicator"], as_index=False
    )["Total Population"].sum()
    
    msa_tables = {}
    
    for msa, g in agg.groupby("metro_title", sort=True):
        p = g.pivot_table(
            index="Race/Sex Indicator", 
            values="Total Population", 
            aggfunc="sum", 
            fill_value=0
        ).reindex(DEMOGRAPHIC_CATEGORIES)

        # Calculate male proportions
        male_total = p.loc[["White male", "Black male", "Other races male"]].sum().item()
        male_white = 0 if male_total == 0 else p.loc["White male"].item() / male_total * 100
        male_black = 0 if male_total == 0 else p.loc["Black male"].item() / male_total * 100
        male_other = 0 if male_total == 0 else p.loc["Other races male"].item() / male_total * 100

        # Calculate female proportions
        female_total = p.loc[["White female", "Black female", "Other races female"]].sum().item()
        female_white = 0 if female_total == 0 else p.loc["White female"].item() / female_total * 100
        female_black = 0 if female_total == 0 else p.loc["Black female"].item() / female_total * 100
        female_other = 0 if female_total == 0 else p.loc["Other races female"].item() / female_total * 100

        proportions = pd.DataFrame(
            {
                "White": [male_white, female_white],
                "Black": [male_black, female_black],
                "Other": [male_other, female_other],
            },
            index=["Male", "Female"],
        ).round(2)
        
        msa_tables[msa] = proportions
    
    return msa_tables


def prepare_2022_tables(min_df_2022: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Prepare proportional demographics tables for 2022 data.
    
    Args:
        min_df_2022: Raw 2022 population data
    
    Returns:
        Dictionary mapping MSA names to demographics proportion tables
    """
    msa_totals = min_df_2022.groupby("metro_title", as_index=False)[
        DEMOGRAPHIC_AGG_COLS
    ].sum()

    # Calculate male proportions
    male_props = msa_totals[
        ["metro_title", "WAC_MALE", "BAC_MALE", "OTHER_MALE", "TOT_MALE"]
    ].copy()
    male_props[["White", "Black", "Other"]] = male_props[
        ["WAC_MALE", "BAC_MALE", "OTHER_MALE"]
    ].div(male_props["TOT_MALE"], axis=0)
    male_props = male_props[["metro_title", "White", "Black", "Other"]]

    # Calculate female proportions
    female_props = msa_totals[
        ["metro_title", "WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE", "TOT_FEMALE"]
    ].copy()
    female_props[["White", "Black", "Other"]] = female_props[
        ["WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE"]
    ].div(female_props["TOT_FEMALE"], axis=0)
    female_props = female_props[["metro_title", "White", "Black", "Other"]]

    # Combine into tables
    msa_tables = {}
    for msa in msa_totals["metro_title"]:
        male_row = male_props.loc[
            male_props["metro_title"] == msa, ["White", "Black", "Other"]
        ].squeeze()
        female_row = female_props.loc[
            female_props["metro_title"] == msa, ["White", "Black", "Other"]
        ].squeeze()

        proportions = pd.DataFrame(
            [male_row.to_numpy(), female_row.to_numpy()],
            index=["Male", "Female"],
            columns=["White", "Black", "Other"]
        ).astype(float)
        proportions = (proportions * 100).round(2)
        
        msa_tables[msa] = proportions
    
    return msa_tables


def render_demographics_comparison(merged_pop_1980: pd.DataFrame, 
                                  min_df_2022: pd.DataFrame) -> None:
    """
    Render the complete demographics comparison section with interactive dropdown.
    
    Args:
        merged_pop_1980: 1980 population data
        min_df_2022: 2022 population data
    """
    # Prepare tables
    msa_tables_1980 = prepare_1980_tables(merged_pop_1980)
    msa_tables_2022 = prepare_2022_tables(min_df_2022)
    
    # Get common MSAs
    common_msas = sorted(set(msa_tables_1980.keys()) & set(msa_tables_2022.keys()))
    
    if not common_msas:
        st.warning("No common MSAs found between 1980 and 2022 datasets.")
        return
    
    # Dropdown selection
    selected_msa = st.selectbox(
        "Select a Metropolitan Statistical Area (MSA):", 
        common_msas, 
        index=0
    )
    
    # Section header
    st.markdown(
        "<h3>Population Distribution by Race and Sex (1980 vs 2022)</h3>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "<p class='center-caption'>Compare Male/Female racial shares side-by-side for the selected MSA.</p>", 
        unsafe_allow_html=True
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
        msa_tables_1980[selected_msa],
        msa_tables_2022[selected_msa],
        selected_msa
    )
    st.altair_chart(bar_chart, use_container_width=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
