"""Data loading utilities for MSA Dashboard

Handles robust CSV loading with multiple path attempts and helpful error messages
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def try_read_csv(path: Path, file_label: str = "file") -> pd.DataFrame | None:
    """Attempt to read a CSV file from multiple possible paths.

    Args:
        path: List of file paths to try
        file_label: Descriptive label for the file (used in messages)

    Returns:
        DataFrame if successful, None otherwise
    """
    path = path.expanduser()

    if path.exists():
        try:
            df_expanded: pd.DataFrame = pd.read_csv(path)
            logging.info(f"✓ Loaded {file_label} from {path}")
            return df_expanded
        except Exception as e:
            logging.error(f"✗ Failed to read {file_label} at {path}: {e}")
            return None
    else:
        st.error(f"❌ Missing {file_label}: expected at {path}")
        return None


def load_main_data(data_paths: Path) -> pd.DataFrame | None:
    """Load and preprocess the main MSA dataset.

    Args:
        data_paths: List of possible file paths

    Returns:
        Preprocessed DataFrame or None if loading fails
    """
    df_data_paths: pd.DataFrame | None = try_read_csv(data_paths, "main MSA dataset")

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
    data_paths: Path,
    merged_paths: Path,
    gdp_paths: Path,
) -> dict:
    """Load all datasets required by the dashboard.

    Args:
        data_paths: Path to main dataset
        merged_paths: Path to merged BFI dataset
        gdp_paths: Path to GDP dataset

    Returns:
        Dictionary with dataset names as keys and DataFrames as values
    """
    datasets: dict[str, pd.DataFrame | None] = {}

    # Load main dataset (required)
    datasets["main"] = load_main_data(data_paths)

    # Load optional datasets
    datasets["merged"] = try_read_csv(
        merged_paths, "merged BFI dataset and 1980/2022 population and labor force data"
    )

    datasets["gdp"] = try_read_csv(gdp_paths, "GDP dataset")

    return datasets
