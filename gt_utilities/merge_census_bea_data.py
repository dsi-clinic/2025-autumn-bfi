"""Supplementary analysis using 1980 and 2022 population and labor data.

This file first groups cleaned supplementary data by general MSA codes,
filters them by MSAs in the BFI dataset, then merges 1980 population,
2022 population, and aggregated labor data individually with BFI data.
"""

import logging
import os
from pathlib import Path

import pandas as pd

from gt_utilities import get_census_bea_data as getter
from gt_utilities import setup_logger

LOGGER: logging.Logger = setup_logger(__name__)

DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "data")).resolve()
RAW_DATA_DIR: Path = DATA_DIR / "raw_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def merge_pop_1980_with_cbsa(
    pop_1980: pd.DataFrame, msa_county: pd.DataFrame
) -> pd.DataFrame | None:
    """Merge cleaned 1980 population data with CBSA–county crosswalk.

    Inputs:
        pop_1980: cleaned 1980 population dataframe
        msa_county: cleaned CBSA–county crosswalk dataframe

    Returns:
        merged dataframe or None if merge fails
    """
    LOGGER.info("Merging 1980 Pop with CBSA Crosswalk...")

    try:
        merged: pd.DataFrame = pop_1980.merge(
            msa_county[["cbsacode", "fips", "cbsaname"]],
            left_on="FIPS State and County Codes",
            right_on="fips",
            how="inner",
        ).drop(columns=["FIPS State and County Codes"])

        LOGGER.info("Merge complete. Result shape: %s", merged.shape)
        return merged
    except Exception as exc:
        LOGGER.error("Error merging 1980 pop with crosswalk: %s", exc, exc_info=True)
        return None


def merge_pop_1980_with_bfi(
    msa_pop_1980: pd.DataFrame, bfi_df: pd.DataFrame
) -> pd.DataFrame | None:
    """Only keeps rows with MSAs relevant/matching to those in the original BFI dataset.

    Returns a subset of the original dataframe that matches that requirement
    """
    LOGGER.info("Filtering 1980 Pop to match BFI MSAs...")

    try:
        merged_pop_1980: pd.DataFrame = msa_pop_1980.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="cbsacode",
            right_on="metro13",
            how="inner",
        ).drop(columns=["cbsacode", "cbsaname"])

        LOGGER.info(
            "Filtered 1980 data to %d rows matching BFI MSAs.", len(merged_pop_1980)
        )
        return merged_pop_1980
    except Exception as exc:
        LOGGER.error("Error merging with BFI: %s", exc, exc_info=True)
        return None


def merge_pop_2022_with_bfi(
    pop2: pd.DataFrame, bfi_df: pd.DataFrame
) -> pd.DataFrame | None:
    """Only keeps rows with MSAs relevant/matching to those in the original BFI dataset."""
    LOGGER.info("Beginning merge of 2022 population data with BFI MSA information.")

    try:
        before_rows: int = pop2.shape[0]
        LOGGER.info("msa_pop_2022 has %d rows before merge.", before_rows)

        merged_pop_2022: pd.DataFrame = pop2.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="CBSA",
            right_on="metro13",
            how="inner",
        ).drop(columns=["CBSA", "NAME"])

        after_rows: int = merged_pop_2022.shape[0]
        LOGGER.info(
            "Merge complete. Rows: %d -> %d (kept %.2f%%).",
            before_rows,
            after_rows,
            100 * after_rows / before_rows if before_rows > 0 else 0,
        )
        return merged_pop_2022

    except KeyError as exc:
        LOGGER.error("KeyError during merge. Expected columns missing: %s", exc)
        LOGGER.error("Available pop2 columns: %s", pop2.columns.tolist())
        LOGGER.error("Available bfi_df columns: %s", bfi_df.columns.tolist())
        return None

    except Exception:
        LOGGER.error(
            "Unexpected error merging 2022 population data with BFI dataset.",
            exc_info=True,
        )
        return None


def combine_industries() -> pd.DataFrame | None:
    """Combines 1980 and 2022 industry labor datasets."""
    LOGGER.info("Combining 1980 and 2022 industry datasets...")

    ind_1980: pd.DataFrame | None = getter.get_industry(1980)
    if ind_1980 is None:
        LOGGER.error("Failed to load 1980 industry data.")
        return None

    ind_2022: pd.DataFrame | None = getter.get_industry(2022)
    if ind_2022 is None:
        LOGGER.error("Failed to load 2022 industry data.")
        return None

    try:
        all_ind: pd.DataFrame = pd.concat([ind_1980, ind_2022], ignore_index=True)
        LOGGER.info(
            "Successfully combined industry datasets. Final row count: %d", len(all_ind)
        )
        return all_ind
    except Exception:
        LOGGER.error(
            "Failed to concatenate 1980 and 2022 industry datasets.", exc_info=True
        )
        return None


def merge_industry_with_msa(
    all_ind: pd.DataFrame, msa_county: pd.DataFrame, bfi_df: pd.DataFrame
) -> pd.DataFrame | None:
    """Adds CBSA/MSA codes to industry data and filters to only the MSAs the BFI dataset.

    Keeps only rows where own_title == 'Total Covered'.

    Parameters:
        all_ind (pd.DataFrame): Combined industry dataset (1980 + 2022)
        msa_county (pd.DataFrame): CBSA–county crosswalk with fips + cbsacode
        bfi_df (pd.DataFrame): BFI dataset containing metro13 + metro_title

    Returns:
        pd.DataFrame or None
    """
    LOGGER.info("Starting merge of industry data with MSA crosswalk...")

    # check required columns
    required_cols_ind: set[str] = {"area_fips"}
    required_cols_cross: set[str] = {"cbsacode", "fips", "cbsaname"}
    required_cols_bfi: set[str] = {"metro13", "metro_title"}

    if not required_cols_ind.issubset(all_ind.columns):
        LOGGER.error("Missing required columns in industry data: %s", required_cols_ind)
        return None

    if not required_cols_cross.issubset(msa_county.columns):
        LOGGER.error(
            "Missing required columns in MSA crosswalk: %s", required_cols_cross
        )
        return None

    if not required_cols_bfi.issubset(bfi_df.columns):
        LOGGER.error("Missing required columns in BFI dataset: %s", required_cols_bfi)
        return None

    # first merge: industry ↔ MSA crosswalk
    try:
        msa_all_ind: pd.DataFrame = all_ind.merge(
            msa_county[["cbsacode", "fips", "cbsaname"]],
            left_on="area_fips",
            right_on="fips",
            how="inner",
        ).drop(columns=["area_fips"])

        LOGGER.info(
            "Merge 1 (Ind <-> MSA Crosswalk) complete. Rows: %d -> %d",
            len(all_ind),
            len(msa_all_ind),
        )
    except Exception:
        LOGGER.error("Failed merging industry data with MSA crosswalk", exc_info=True)
        return None

    # second merge: keep only MSAs in BFI dataset
    try:
        merged_all_ind: pd.DataFrame = msa_all_ind.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="cbsacode",
            right_on="metro13",
            how="inner",
        ).drop(
            columns=["cbsacode", "cbsaname", "fips", "industry_title"], errors="ignore"
        )

        LOGGER.info(
            "Merge 2 (Ind <-> BFI) complete. Rows: %d -> %d",
            len(msa_all_ind),
            len(merged_all_ind),
        )
    except Exception:
        LOGGER.error("Failed merging MSA industry data with BFI dataset", exc_info=True)
        return None

    # keep only Total Covered
    try:
        before: int = len(merged_all_ind)
        if "own_title" in merged_all_ind.columns:
            merged_all_ind = merged_all_ind.query('`own_title` == "Total Covered"')
            LOGGER.info(
                'Filtered rows where own_title == "Total Covered": %d -> %d',
                before,
                len(merged_all_ind),
            )
        else:
            LOGGER.warning("'own_title' column missing. Skipping filter.")

        return merged_all_ind
    except Exception:
        LOGGER.error("Failed filtering to own_title == 'Total Covered'", exc_info=True)
        return None
