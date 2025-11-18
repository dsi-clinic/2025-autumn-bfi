"""Data loading utilities for MSA Dashboard

Handles robust CSV loading with multiple path attempts and helpful error messages
"""

import logging

import pandas as pd
import Path
import streamlit as st

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def try_read_csv(
    possible_paths: list[str], file_label: str = "file"
) -> pd.DataFrame | None:
    """Attempt to read a CSV file from multiple possible paths.

    Args:
        possible_paths: List of file paths to try
        file_label: Descriptive label for the file (used in messages)

    Returns:
        DataFrame if successful, None otherwise
    """
    for p in possible_paths:
        try:
            p_expanded = Path.expanduser(p)
            if Path.exists(p_expanded):
                df_expanded = pd.read_csv(p_expanded)
                logging.info(f"✓ Loaded {file_label} from {p_expanded}")
                return df_expanded
        except Exception as e:
            logging.warning(f"✗ Failed to read {p} ({e})")

    # If we get here, none of the paths worked
    st.error(f"❌ Could not locate {file_label}. Tried: {possible_paths}")
    return None


def load_main_data(data_paths: list[str]) -> pd.DataFrame | None:
    """Load and preprocess the main MSA dataset.

    Args:
        data_paths: List of possible file paths

    Returns:
        Preprocessed DataFrame or None if loading fails
    """
    df_data_paths = try_read_csv(data_paths, "main MSA dataset")

    if df_data_paths is None:
        return None

    # Trim original notebook slicing if present
    try:
        df_data_paths = df_data_paths.iloc[33:].reset_index(drop=True)
        logging.info("Applied row slicing (removed first 33 rows)")
    except Exception as e:
        logging.warning(f"Could not apply row slicing: {e}")

    return df_data_paths


def load_all_datasets(
    data_paths: list[str],
    cleaned_paths: list[str],
    merged_1980_paths: list[str],
    min_2022_paths: list[str],
    gdp_paths: list[str],
) -> dict:
    """Load all datasets required by the dashboard.

    Returns:
        Dictionary with dataset names as keys and DataFrames as values
    """
    datasets = {}

    # Load main dataset (required)
    datasets["main"] = load_main_data(data_paths)

    # Load optional datasets
    datasets["cleaned"] = try_read_csv(cleaned_paths, "cleaned dataset (for chart 6)")
    datasets["merged_1980"] = try_read_csv(
        merged_1980_paths, "merged_pop_1980 (1980 population)"
    )
    datasets["min_2022"] = try_read_csv(min_2022_paths, "min_df_2022 (2022 population)")
    datasets["gdp"] = try_read_csv(gdp_paths, "GDP dataset")

    return datasets
