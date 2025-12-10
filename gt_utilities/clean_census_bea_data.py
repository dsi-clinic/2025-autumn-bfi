"""Supplementary analysis using 1980 and 2022 population and labor data.

This file reformats cleaned supplementary data to prepare for merging
with BFI data.
"""

import logging
import os
from pathlib import Path

import pandas as pd

DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "data")).resolve()
RAW_DATA_DIR: Path = DATA_DIR / "raw_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Logger
LOGGER: logging.Logger = logging.getLogger(__name__)


def clean_bfi(bfi_df: pd.DataFrame) -> pd.DataFrame | None:
    """Turns MSAs in the original BFI dataset into string

    Returns the same BFI dataframe, but with metro13 entries as strings
    """
    LOGGER.info("Cleaning BFI dataset...")
    if "metro13" not in bfi_df.columns:
        LOGGER.error("Column 'metro13' missing from BFI data.")
        return None

    try:
        bfi_df["metro13"] = (
            pd.to_numeric(bfi_df["metro13"], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(5)
        )
        LOGGER.info("Converted 'metro13' to 5-digit strings.")
        return bfi_df
    except Exception as exc:
        LOGGER.error("Error cleaning BFI data: %s", exc, exc_info=True)
        return None


def clean_pop_1980(pop: pd.DataFrame) -> pd.DataFrame | None:
    """This function does the following cleaning:

    1. Queries raw dataset containing 1980 population data to become
    a dataframe with only 1980 data.
    2. Add column for each row that sums up all population counts
    across each age range within that row. Called 'Total Population'.
    3. Transforms all FIPS codes into 5 character strings (adds leading
    zeros if original number not 5 characters long).
    """
    LOGGER.info("Cleaning 1980 population data...")
    required_cols: list[str] = ["Year of Estimate", "FIPS State and County Codes"]
    for col in required_cols:
        if col not in pop.columns:
            LOGGER.error("Missing required column '%s' in population data.", col)
            return None

    try:
        # Filter 1980
        pop_1980: pd.DataFrame = pop.query(
            "`Year of Estimate` == 1980"
        ).copy()  # Use .copy() to avoid SettingWithCopy warning

        # Calculate Total Population (Summing cols 3 onwards)
        cols_to_sum: list[str] = list(pop_1980.columns)[3:]
        pop_1980["Total Population"] = pop_1980[cols_to_sum].sum(axis=1)

        # Format FIPS
        pop_1980["FIPS State and County Codes"] = (
            pd.to_numeric(pop_1980["FIPS State and County Codes"], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(5)
        )

        LOGGER.info("Cleaned 1980 data. Rows: %d", len(pop_1980))
        return pop_1980
    except Exception as exc:
        LOGGER.error("Error cleaning 1980 data: %s", exc, exc_info=True)
        return None


def clean_cbsa_county_crosswalk(msa_county: pd.DataFrame) -> pd.DataFrame | None:
    """Creates FIPS codes and cleans CBSA codes."""
    LOGGER.info("Cleaning crosswalk data...")

    required: list[str] = ["fipst", "fipscounty", "cbsa"]
    if not all(col in msa_county.columns for col in required):
        LOGGER.error("Missing columns in crosswalk. Required: %s", required)
        return None

    try:
        # Create full FIPS
        msa_county["fips"] = (
            pd.to_numeric(msa_county["fipscounty"], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(4)
        )

        # Clean CBSA
        msa_county["cbsacode"] = (
            pd.to_numeric(msa_county["cbsa"], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(5)
        )
        LOGGER.info("Crosswalk cleaned. Added 'fips' and formatted 'cbsacode'.")
        return msa_county
    except Exception as exc:
        LOGGER.error("Error cleaning crosswalk: %s", exc, exc_info=True)
        return None


def aggregate_pop_1980(merged_pop_1980: pd.DataFrame) -> pd.DataFrame | None:
    """Aggregates 1980 population data to the MSA level.

    Sums across all counties (FIPS) for each Race/Sex category.

    Returns:
        Aggregated dataframe or None if the aggregation fails.
    """
    LOGGER.info("Aggregating 1980 Pop to MSA level...")

    group_cols: list[str] = [
        "Year of Estimate",
        "Race/Sex Indicator",
        "metro13",
        "metro_title",
    ]

    try:
        pop_1980_agg: pd.DataFrame = (
            merged_pop_1980.drop(columns=["fips"], errors="ignore")
            .groupby(group_cols, as_index=False)
            .sum(numeric_only=True)
        )
        LOGGER.info("Aggregation complete. Result shape: %s", pop_1980_agg.shape)
        return pop_1980_agg
    except Exception as exc:
        LOGGER.error("Error aggregating 1980 data: %s", exc, exc_info=True)
        return None


def transform_pop_1980_to_final(pop_1980_agg: pd.DataFrame) -> pd.DataFrame | None:
    """Transforms aggregated 1980 MSA population data to wide format.

    Final long-then-wide format has MSA totals, gender totals,
    and race/sex breakdowns.
    """
    LOGGER.info("Transforming 1980 aggregated data to final wide format...")

    try:
        # Construct age groups list
        age_groups_with_total: list[str] = ["Total Population"] + pop_1980_agg.columns[
            3:-4
        ].to_list()
        id_vars: list[str] = ["Year of Estimate", "metro13", "metro_title"]

        # Melt to long
        long_df: pd.DataFrame = pop_1980_agg.melt(
            id_vars=id_vars + ["Race/Sex Indicator"],
            value_vars=age_groups_with_total,
            var_name="AGEGRP",
            value_name="Population",
        )

        # Normalize indicator
        long_df["Race/Sex Indicator"] = (
            long_df["Race/Sex Indicator"].astype(str).str.strip().str.lower()
        )

        # Compute Totals
        # 1. MSA Totals
        msa_totals: pd.DataFrame = long_df.groupby(
            id_vars + ["AGEGRP"], as_index=False, observed=True
        )["Population"].sum()
        msa_totals["Race/Sex Indicator"] = "MSA Population"

        # 2. Gender Totals
        total_male: pd.DataFrame = (
            long_df[long_df["Race/Sex Indicator"].str.endswith(" male")]
            .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
            .sum()
        )
        total_male["Race/Sex Indicator"] = "Total male"

        total_female: pd.DataFrame = (
            long_df[long_df["Race/Sex Indicator"].str.endswith(" female")]
            .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
            .sum()
        )
        total_female["Race/Sex Indicator"] = "Total female"

        # Combine
        long_augmented: pd.DataFrame = pd.concat(
            [long_df, msa_totals, total_male, total_female], ignore_index=True
        )

        # Pivot to Wide
        pop_1980_wide: pd.DataFrame = long_augmented.pivot_table(
            index=id_vars + ["AGEGRP"],
            columns="Race/Sex Indicator",
            values="Population",
            aggfunc="sum",
        ).reset_index()
        pop_1980_wide.columns.name = None

        # Map AGEGRP to IDs
        age_id_map: dict[str, int] = {
            name: i for i, name in enumerate(age_groups_with_total)
        }
        pop_1980_wide["AGEGRP"] = (
            pop_1980_wide["AGEGRP"].map(age_id_map).astype("Int64")
        )

        LOGGER.info("Transformation complete. Final shape: %s", pop_1980_wide.shape)
        return pop_1980_wide

    except Exception as exc:
        LOGGER.error("Error transforming 1980 data: %s", exc, exc_info=True)
        return None


def rename_pop_1980_columns(final_pop_1980: pd.DataFrame) -> pd.DataFrame | None:
    """Renames columns in the 1980 final population table to match 2022 naming."""
    rename_map: dict[str, str] = {
        "MSA Population": "TOT_POP",
        "Total male": "TOT_MALE",
        "Total female": "TOT_FEMALE",
        "Black female": "BAC_FEMALE",
        "Black male": "BAC_MALE",
        "Other races female": "OTHER_FEMALE",
        "Other races male": "OTHER_MALE",
        "White female": "WAC_FEMALE",
        "White male": "WAC_MALE",
        "Year of Estimate": "year",
    }

    try:
        final_pop_1980_renamed: pd.DataFrame = final_pop_1980.rename(columns=rename_map)
        LOGGER.info("Renamed 1980 columns to 2022 standard.")
        return final_pop_1980_renamed
    except Exception as exc:
        LOGGER.error("Error renaming columns: %s", exc, exc_info=True)
        return None


def clean_pop_2022(pop2: pd.DataFrame) -> pd.DataFrame | None:
    """Turns CBSAs in the original pop_2022 dataset into string."""
    LOGGER.info("Starting pop_2022 cleaning — converting CBSA to 5-digit strings.")

    if "CBSA" not in pop2.columns:
        LOGGER.error("Column 'CBSA' not found in pop_2022 dataframe.")
        return None

    try:
        pop2["CBSA"] = (
            pd.to_numeric(pop2["CBSA"], errors="coerce")
            .astype("Int64")  # allows NA safely
            .astype(str)
            .str.zfill(5)
        )

        LOGGER.info("Successfully cleaned CBSA column to 5-digit strings.")
        return pop2

    except Exception:
        LOGGER.error("Failed while cleaning CBSA in pop_2022 dataset.", exc_info=True)
        return None


def organize_pop_2022_minimal(merged_pop_2022: pd.DataFrame) -> pd.DataFrame | None:
    """Restructures merged 2022 population data into MSA totals by race/sex.

    Returns a cleaned dataframe with:
    metro13, metro_title,
    TOT_POP, TOT_MALE, TOT_FEMALE,
    WAC_MALE, WAC_FEMALE,
    BAC_MALE, BAC_FEMALE,
    OTHER_MALE, OTHER_FEMALE
    """
    LOGGER.info("Beginning 2022 minimal-category restructuring.")

    required_base_cols: list[str] = [
        "AGEGRP",
        "metro13",
        "metro_title",
        "TOT_POP",
        "TOT_MALE",
        "TOT_FEMALE",
        "WAC_MALE",
        "WAC_FEMALE",
        "BAC_MALE",
        "BAC_FEMALE",
    ]

    required_other_m: list[str] = ["IAC_MALE", "AAC_MALE", "NAC_MALE", "H_MALE"]
    required_other_f: list[str] = ["IAC_FEMALE", "AAC_FEMALE", "NAC_FEMALE", "H_FEMALE"]

    # --- Check required columns ---
    missing_cols: list[str] = [
        c
        for c in required_base_cols + required_other_m + required_other_f
        if c not in merged_pop_2022.columns
    ]
    if missing_cols:
        LOGGER.error(
            "Missing required columns for 2022 restructuring: %s", missing_cols
        )
        return None

    try:
        # filter AGEGRP == 0 (Total Age)
        before: int = merged_pop_2022.shape[0]
        min_df_2022: pd.DataFrame = merged_pop_2022.query("`AGEGRP` == 0").copy()
        after: int = min_df_2022.shape[0]
        LOGGER.info("Filtered AGEGRP==0: %d -> %d rows.", before, after)

        # select base columns
        min_df_2022 = min_df_2022[
            [
                "metro13",
                "metro_title",
                "TOT_POP",
                "TOT_MALE",
                "TOT_FEMALE",
                "WAC_MALE",
                "WAC_FEMALE",
                "BAC_MALE",
                "BAC_FEMALE",
            ]
        ]

        # compute OTHER_MALE and OTHER_FEMALE
        min_df_2022["OTHER_MALE"] = merged_pop_2022.loc[
            min_df_2022.index, required_other_m
        ].sum(axis=1)
        min_df_2022["OTHER_FEMALE"] = merged_pop_2022.loc[
            min_df_2022.index, required_other_f
        ].sum(axis=1)

        LOGGER.info("Computed OTHER_MALE and OTHER_FEMALE aggregates.")
        LOGGER.info("Successfully created minimal 2022 dataset: %s", min_df_2022.shape)

        return min_df_2022

    except Exception as exc:
        LOGGER.error("Failed during 2022 restructuring: %s", exc, exc_info=True)
        return None
