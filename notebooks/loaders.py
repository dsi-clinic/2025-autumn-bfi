"""
Data loading utilities for MSA Dashboard
Handles robust CSV loading with multiple path attempts and helpful error messages
"""
import os
import logging
from typing import List, Optional

import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def try_read_csv(possible_paths: List[str], file_label: str = "file") -> Optional[pd.DataFrame]:
    """
    Attempt to read a CSV file from multiple possible paths.
    
    Args:
        possible_paths: List of file paths to try
        file_label: Descriptive label for the file (used in messages)
    
    Returns:
        DataFrame if successful, None otherwise
    """
    for p in possible_paths:
        try:
            p_expanded = os.path.expanduser(p)
            if os.path.exists(p_expanded):
                df = pd.read_csv(p_expanded)
                logging.info(f"✓ Loaded {file_label} from {p_expanded}")
                return df
        except Exception as e:
            logging.warning(f"✗ Failed to read {p} ({e})")
    
    # If we get here, none of the paths worked
    st.error(f"❌ Could not locate {file_label}. Tried: {possible_paths}")
    return None


def load_main_data(data_paths: List[str]) -> Optional[pd.DataFrame]:
    """
    Load and preprocess the main MSA dataset.
    
    Args:
        data_paths: List of possible file paths
    
    Returns:
        Preprocessed DataFrame or None if loading fails
    """
    df = try_read_csv(data_paths, "main MSA dataset")
    
    if df is None:
        return None
    
    # Trim original notebook slicing if present
    try:
        df = df.iloc[33:].reset_index(drop=True)
        logging.info("Applied row slicing (removed first 33 rows)")
    except Exception as e:
        logging.warning(f"Could not apply row slicing: {e}")
    
    return df


def load_all_datasets(data_paths, cleaned_paths, merged_1980_paths, 
                      min_2022_paths, gdp_paths) -> dict:
    """
    Load all datasets required by the dashboard.
    
    Returns:
        Dictionary with dataset names as keys and DataFrames as values
    """
    datasets = {}
    
    # Load main dataset (required)
    datasets['main'] = load_main_data(data_paths)
    
    # Load optional datasets
    datasets['cleaned'] = try_read_csv(cleaned_paths, "cleaned dataset (for chart 6)")
    datasets['merged_1980'] = try_read_csv(merged_1980_paths, "merged_pop_1980 (1980 population)")
    datasets['min_2022'] = try_read_csv(min_2022_paths, "min_df_2022 (2022 population)")
    datasets['gdp'] = try_read_csv(gdp_paths, "GDP dataset")
    
    return datasets
