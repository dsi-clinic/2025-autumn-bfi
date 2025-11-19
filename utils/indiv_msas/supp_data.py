"""Supplementary analysis using 1980 and 2022 population and labor data.

This file first obtains raw data and saves them in /data/raw_data and then
cleans and retrieves them, reformatting them into tables
"""

import io
import logging
import os
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.exceptions import ReadTimeout, RequestException

DATA_DIR = Path(os.environ["DATA_DIR"])
RAW_DATA_DIR = Path(os.environ["RAW_DATA_DIR"])
LOGGER = logging.getLogger(__name__)

# Make raw data urls hyper-parameters within dictionaries
RAW_CENSUS_POP_DATA_URLS = {
    "https://www2.census.gov/programs-surveys/popest/datasets/"
    "1980-1990/counties/asrh/pe-02.csv": "1980",
    "https://www2.census.gov/programs-surveys/popest/datasets/"
    "2020-2023/metro/asrh/cbsa-est2023-alldata-char.csv": "2022",
}

UBLA_LABOR_DATA_ZIP_URLS_AND_RAW_PATHS = {
    "https://data.bls.gov/cew/data/files/1980/sic/csv/"
    "sic_1980_annual_by_industry.zip": "sic.1980.annual.by_industry/"
    "sic.1980.annual 0Z (All Industries).csv",
    "https://data.bls.gov/cew/data/files/2022/csv/"
    "2022_annual_by_industry.zip": "2022.annual.by_industry/"
    "2022.annual 10 10 Total, all industries.csv",
}

NBER_COUNTY_CBSA_CROSSWALK_URL = (
    "https://data.nber.org/cbsa-csa-fips-county-crosswalk/cbsa2fipsxw.csv"
)


def get_census_pop(data_urls: dict[str, str] = RAW_CENSUS_POP_DATA_URLS) -> None:
    """Gets csvs containing 1980 and 2022 population data.

    From US Census Bureau at:
    https://www2.census.gov/programs-surveys/popest/
    """
    for url, year in data_urls.items():
        # gets data from URL
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
        except ReadTimeout as exc:
            LOGGER.error(f"Timed out while downloading {year} census data from {url}")
            LOGGER.exception(exc)
            continue
        except RequestException as exc:
            LOGGER.error(f"Failed to download {year} population data from", url)
            LOGGER.exception(exc)
            return

        # saves raw data
        output_file = RAW_DATA_DIR / f"pop_{year}.csv"

        try:
            with output_file.open("wb") as f:
                f.write(r.content)
        except OSError as exc:
            LOGGER.error("Failed to write output file: %s", output_file)
            LOGGER.exception(exc)
            return

        LOGGER.info(f"Saved pop_{year}.csv to", output_file.resolve())
    return


def get_ubls_labor(
    zip_urls: dict[str, str] = UBLA_LABOR_DATA_ZIP_URLS_AND_RAW_PATHS,
) -> None:
    """Unzips folder containing 1980 employment data for all industries.

    From US Bureau of Labor Statistics at:
    https://www.bls.gov/cew/downloadable-data-files.htm
    """
    for zip_url, path in zip_urls.items():
        # get year of data
        if "1980" in zip_url:
            year = "1980"
        else:
            year = "2022"

        # get zipfile containing data
        try:
            r = requests.get(zip_url, timeout=30)
            r.raise_for_status()
        except RequestException as exc:
            LOGGER.error(
                f"Failed to download {year} labor data zipfile from %s", zip_url
            )
            LOGGER.exception(exc)
            return

        # unzip and save raw data
        output_file = RAW_DATA_DIR / f"labor_{year}.csv"

        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                with (
                    z.open(path) as source,
                    output_file.open("wb") as target,
                ):
                    target.write(source.read())

        except zipfile.BadZipFile:
            LOGGER.error("The downloaded file is not a valid ZIP archive.")
            return

        except KeyError:
            LOGGER.error("Expected file was NOT found inside the ZIP:\n", path)
            return

        except OSError as exc:
            LOGGER.error("Failed to write output file: %s", output_file)
            LOGGER.exception(exc)
            return

        LOGGER.info(f"Saved labor_{year}.csv to", output_file.resolve())
    return


def get_uber_county_cbsa_crosswalk(
    url: str = NBER_COUNTY_CBSA_CROSSWALK_URL,
) -> None:
    """Saves csv containing 2013 cbsa to county crosswalk

    From National Bureau of Economic Research at:
    https://data.nber.org/cbsa-msa-fips-ssa-county-crosswalk/2013/
    """
    # get data from url
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()

    except ReadTimeout as exc:
        LOGGER.error(f"Timed out while downloading 2013 crosswalk data from {url}")
        LOGGER.exception(exc)
        return

    except RequestException as exc:
        LOGGER.error("Failed to download 2013 crosswalk data from", url)
        LOGGER.exception(exc)
        return

    # saves raw data
    output_file = RAW_DATA_DIR / "cbsatocountycrosswalk.csv"

    try:
        with output_file.open("wb") as f:
            f.write(r.content)
    except OSError as exc:
        LOGGER.error("Failed to write output file: %s", output_file)
        LOGGER.exception(exc)
        return

    LOGGER.info("Saved cbsatocountycrosswalk.csv to", output_file.resolve())
    return


def get_pop_1980() -> pd.DataFrame:
    """Retrieves pop_1980.csv from data/raw_data.

    Ignores the first couple rows because they contain informational
    text and not actual data. Separately removes the first row,
    which is empty, in order to maintain column names.

    Returns a uncleaned dataframe from pop_1980.csv
    """
    csv_path = RAW_DATA_DIR / "pop_1980.csv"
    LOGGER.info("Attempting to load 1980 population data from %s", csv_path)

    try:
        pop = pd.read_csv(csv_path, skiprows=5, header=0)
        LOGGER.info("Successfully read pop_1980.csv (initial shape: %s)", pop.shape)

        # Drop the first empty row
        pop = pop.drop(0)
        LOGGER.info("Dropped initial empty row. Final shape: %s", pop.shape)

        return pop

    except FileNotFoundError:
        LOGGER.error("pop_1980.csv not found at %s", csv_path)
        return None

    except pd.errors.EmptyDataError:
        LOGGER.error("pop_1980.csv exists but is empty or unreadable.")
        return None

    except Exception as exc:
        LOGGER.error("Unexpected error while importing pop_1980.csv")
        LOGGER.exception(exc)
        return None


def get_bfi() -> pd.DataFrame:
    """Retrieves original bfi csv from data folder.

    Returns the csv as a dataframe.
    """
    csv_path = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
    LOGGER.info("Attempting to load BFI data from %s", csv_path)

    try:
        bfi_df = pd.read_csv(csv_path)
        LOGGER.info("Successfully read BFI csv (initial shape: %s)", bfi_df.shape)

        return bfi_df

    except FileNotFoundError:
        LOGGER.error(
            "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv not found at %s",
            csv_path,
        )
        return None

    except pd.errors.EmptyDataError:
        LOGGER.error(
            "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv exists but is empty or unreadable."
        )
        return None

    except Exception as exc:
        LOGGER.error(
            "Unexpected error while importing the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
        )
        LOGGER.exception(exc)
        return None


def clean_bfi(bfi_df: pd.DataFrame) -> pd.DataFrame:
    """Turns MSAs in the original BFI dataset into string

    Returns the same BFI dataframe, but with metro13 entries as strings
    """
    LOGGER.info("Starting BFI cleaning — converting metro13 to 5-digit strings.")

    if "metro13" not in bfi_df.columns:
        LOGGER.error("Column 'metro13' not found in BFI dataframe.")
        return None
    try:
        bfi_df["metro13"] = (
            pd.to_numeric(bfi_df["metro13"], errors="coerce")
            .astype("Int64")  # allows NA safely
            .astype(str)
            .str.zfill(5)
        )

        LOGGER.info("Successfully cleaned metro13 column to 5-digit strings.")

    except Exception as exc:
        LOGGER.error("Failed while cleaning metro13 in BFI dataset.")
        LOGGER.exception(exc)
        return None

    return bfi_df


def clean_pop_1980(pop: pd.DataFrame) -> pd.DataFrame:
    """This function does the following cleaning:

    1. Queries raw dataset containing 1980 population data to become
    a dataframe with only 1980 data.
    2. Add column for each row that sums up all population counts
    across each age range within that row. Called 'Total Population'.
    3. Transforms all FIPS codes into 5 character strings (adds leading
    zeros if original number not 5 characters long).
    """
    LOGGER.info("Starting cleaning for 1980 population dataset...")

    # validate required columns
    required_cols = ["Year of Estimate", "FIPS State and County Codes"]
    for col in required_cols:
        if col not in pop.columns:
            LOGGER.error("Missing required column '%s' in population data.", col)
            return None

    # filter to only 1980
    try:
        pop_1980 = pop.query("`Year of Estimate` == 1980")
        LOGGER.info("Filtered to 1980: %d rows remain.", len(pop_1980))
    except Exception as exc:
        LOGGER.error("Error filtering rows for Year == 1980")
        LOGGER.exception(exc)
        return None

    if pop_1980.empty:
        LOGGER.warning("No rows found for Year of Estimate == 1980.")
        return pop_1980

    # add Total Population
    try:
        # All population columns start from index 3 onward
        cols_to_sum = list(pop_1980.columns)[3:]
        LOGGER.info(
            "Summing %d population columns to create 'Total Population'.",
            len(cols_to_sum),
        )

        pop_1980["Total Population"] = pop_1980[cols_to_sum].sum(axis=1)

    except Exception as exc:
        LOGGER.error("Failed to compute Total Population.")
        LOGGER.exception(exc)
        return None

    # make FIPS 5-digit strings
    try:
        pop_1980["FIPS State and County Codes"] = (
            pd.to_numeric(pop_1980["FIPS State and County Codes"], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(5)
        )
        LOGGER.info("Successfully cleaned FIPS column to 5-digit strings.")

    except Exception as exc:
        LOGGER.error("Failed to convert FIPS codes to 5-digit strings.")
        LOGGER.exception(exc)
        return None

    LOGGER.info(
        "Finished cleaning 1980 population dataset. Final shape: %s", pop_1980.shape
    )
    return pop_1980


def get_cbsa_county_crosswalk() -> pd.DataFrame:
    """Retrieves the cbsa to county crosswalk csv.

    Returns the csv as a dataframe.
    """
    csv_path = RAW_DATA_DIR / "cbsatocountycrosswalk.csv"
    LOGGER.info("Attempting to load BFI data from %s", csv_path)

    try:
        msa_county = pd.read_csv(csv_path, encoding="latin1")
        LOGGER.info(
            "Successfully read cbsatocountycrosswalk.csv (initial shape: %s)",
            msa_county.shape,
        )

        return msa_county

    except FileNotFoundError:
        LOGGER.error("cbsatocountycrosswalk.csv not found at %s", csv_path)
        return None

    except pd.errors.EmptyDataError:
        LOGGER.error("cbsatocountycrosswalk.csv exists but is empty or unreadable.")
        return None

    except Exception as exc:
        LOGGER.error("Unexpected error while importing cbsatocountycrosswalk.csv")
        LOGGER.exception(exc)
        return None


def clean_cbsa_county_crosswalk(msa_county: pd.DataFrame) -> pd.DataFrame:
    """Creates FIPS codes and turns CBSA codes in the original crosswalk dataset into string

    Merges state FIPS and County FIPS to get overall FIPS code and returns the same
    crosswalk dataframe, but with that new column and CBSA entries as strings
    """
    LOGGER.info("Starting FIPS cleaning — Combining State and County FIPS.")

    if "fipsstatecode" not in msa_county.columns:
        LOGGER.error("Column 'fipsstatecode' not found in crosswalk dataframe.")
        return None
    if "fipscountycode" not in msa_county.columns:
        LOGGER.error("Column 'fipscountycode' not found in crosswalk dataframe.")
        return None
    try:
        msa_county["fips"] = (
            pd.to_numeric(msa_county["fipsstatecode"], errors="coerce")
            .astype("Int64")  # allows NA safely
            .astype(str)
            .str.zfill(2)
        ) + (
            pd.to_numeric(msa_county["fipscountycode"], errors="coerce")
            .astype("Int64")  # allows NA safely
            .astype(str)
            .str.zfill(3)
        )

        LOGGER.info("Successfully created FIPS column as 5-digit strings.")

    except Exception as exc:
        LOGGER.error("Failed while creating FIPS in crosswalk dataset.")
        LOGGER.exception(exc)
        return None

    LOGGER.info("Starting CBSA cleaning — converting CBSA codes to 5-digit strings.")

    if "cbsacode" not in msa_county.columns:
        LOGGER.error("Column 'cbsacode' not found in crosswalk dataframe.")
        return None
    try:
        msa_county["cbsacode"] = (
            pd.to_numeric(msa_county["cbsacode"], errors="coerce")
            .astype("Int64")  # allows NA safely
            .astype(str)
            .str.zfill(5)
        )

        LOGGER.info("Successfully convert CBSA column to 5-digit strings.")

    except Exception as exc:
        LOGGER.error("Failed while cleaning CBSA in crosswalk dataset.")
        LOGGER.exception(exc)
        return None

    return msa_county


def merge_pop_1980_with_cbsa(
    pop_1980: pd.DataFrame, msa_county: pd.DataFrame
) -> pd.DataFrame:
    """Merge cleaned 1980 population data with CBSA–county crosswalk.

    Inputs:
        pop_1980: cleaned 1980 population dataframe
        msa_county: cleaned CBSA–county crosswalk dataframe

    Returns:
        merged dataframe or None if merge fails
    """
    LOGGER.info("Starting merge of 1980 population data with CBSA–county crosswalk.")

    # validate expected columns
    required_pop_cols = ["FIPS State and County Codes"]
    required_crosswalk_cols = ["cbsacode", "fips", "cbsatitle"]

    for col in required_pop_cols:
        if col not in pop_1980.columns:
            LOGGER.error("Missing column '%s' in pop_1980 dataframe.", col)
            return None

    for col in required_crosswalk_cols:
        if col not in msa_county.columns:
            LOGGER.error("Missing column '%s' in msa_county dataframe.", col)
            return None

    LOGGER.info(
        "pop_1980 shape before merge: %s | crosswalk shape: %s",
        pop_1980.shape,
        msa_county.shape,
    )

    # merge
    try:
        merged = pop_1980.merge(
            msa_county[["cbsacode", "fips", "cbsatitle"]],
            left_on="FIPS State and County Codes",
            right_on="fips",
            how="inner",
        ).drop(columns=["FIPS State and County Codes"])

        LOGGER.info(
            "Merge completed. Output shape: %s (merged rows: %d)",
            merged.shape,
            len(merged),
        )

        # warn if suspiciously few matches
        if merged.empty:
            LOGGER.warning("Merge produced ZERO rows. Possible FIPS mismatch.")

        return merged

    except Exception as exc:
        LOGGER.error("Failed to merge 1980 population data with CBSA crosswalk.")
        LOGGER.exception(exc)
        return None


def merge_pop_1980_with_bfi(
    msa_pop_1980: pd.DataFrame, bfi_df: pd.DataFrame
) -> pd.DataFrame:
    """Only keeps rows with MSAs relevant/matching to those in the original BFI dataset.

    Returns a subset of the original dataframe that matches that requirement
    """
    LOGGER.info("Beginning merge of 1980 population data with BFI MSA information.")

    try:
        before_rows = msa_pop_1980.shape[0]
        LOGGER.info("msa_pop_1980 has %d rows before merge.", before_rows)

        merged_pop_1980 = msa_pop_1980.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="cbsacode",
            right_on="metro13",
            how="inner",
        ).drop(columns=["cbsacode", "cbsatitle"])

        after_rows = merged_pop_1980.shape[0]
        LOGGER.info(
            "Merge complete. Rows: %d → %d (kept %.2f%%).",
            before_rows,
            after_rows,
            100 * after_rows / before_rows if before_rows > 0 else 0,
        )
        return merged_pop_1980

    except KeyError as exc:
        LOGGER.error("KeyError during merge. Expected columns missing: %s", exc)
        LOGGER.error(
            "Available msa_pop_1980 columns: %s", msa_pop_1980.columns.tolist()
        )
        LOGGER.error("Available bfi_df columns: %s", bfi_df.columns.tolist())
        LOGGER.exception(exc)  # stack trace
        raise

    except Exception as exc:
        LOGGER.error("Unexpected error merging 1980 population data with BFI dataset.")
        LOGGER.exception(exc)
        raise


def aggregate_pop_1980(merged_pop_1980: pd.DataFrame) -> pd.DataFrame:
    """Aggregates 1980 population data to the MSA level.

    Sums across all counties (FIPS) for each Race/Sex category.

    Returns:
        Aggregated dataframe or None if the aggregation fails.
    """
    LOGGER.info("Starting aggregation of 1980 population data to MSA level.")

    # required grouping columns
    group_cols = [
        "Year of Estimate",
        "Race/Sex Indicator",
        "metro13",
        "metro_title",
    ]

    # validate columns
    for col in group_cols:
        if col not in merged_pop_1980.columns:
            LOGGER.error("Missing required grouping column '%s'.", col)
            return None

    if "fips" not in merged_pop_1980.columns:
        LOGGER.warning("Column 'fips' not found — continuing without dropping it.")
    else:
        LOGGER.info("Dropping county-level column 'fips' before aggregation.")

    LOGGER.info(
        "Shape before aggregation: %s | Grouping by columns: %s",
        merged_pop_1980.shape,
        group_cols,
    )

    # aggregate
    try:
        pop_1980_agg = (
            merged_pop_1980.drop(columns=["fips"], errors="ignore")
            .groupby(group_cols, as_index=False)
            .sum(numeric_only=True)
        )

        LOGGER.info(
            "Aggregation completed. Output shape: %s (rows: %d)",
            pop_1980_agg.shape,
            len(pop_1980_agg),
        )

        if pop_1980_agg.empty:
            LOGGER.warning("Aggregation returned ZERO rows. Check grouping keys.")

        return pop_1980_agg

    except Exception as exc:
        LOGGER.error("Failed to aggregate 1980 population data.")
        LOGGER.exception(exc)
        return None


def transform_pop_1980_to_final(
    pop_1980_agg: pd.DataFrame,
) -> pd.DataFrame:  # make 1980 look like 2022 data structure
    """Transforms aggregated 1980 MSA population data

    Final long-then-wide format has MSA totals, gender totals,
    and race/sex breakdowns.
    """
    LOGGER.info("Starting 1980 population long-to-wide transformation.")

    # validate required columns
    required_cols = [
        "Year of Estimate",
        "Race/Sex Indicator",
        "metro13",
        "metro_title",
        "Total Population",
    ]
    for col in required_cols:
        if col not in pop_1980_agg.columns:
            LOGGER.error("Missing required column '%s' in pop_1980_agg.", col)
            return None

    # create age group list
    try:
        age_groups_with_total = ["Total Population"] + pop_1980_agg.columns[
            3:-4
        ].to_list()
        LOGGER.info(
            "Constructed %d age groups including Total Population.",
            len(age_groups_with_total),
        )
    except Exception as exc:
        LOGGER.error("Failed constructing age groups from pop_1980_agg.")
        LOGGER.exception(exc)
        return None

    id_vars = ["Year of Estimate", "metro13", "metro_title"]

    # melt to long format
    try:
        long_df = pop_1980_agg.melt(
            id_vars=id_vars + ["Race/Sex Indicator"],
            value_vars=age_groups_with_total,
            var_name="AGEGRP",
            value_name="Population",
        )
        LOGGER.info("Long-format population created. Shape: %s", long_df.shape)

        if long_df.empty:
            LOGGER.warning("long_df is empty after melt — check input data.")
    except Exception as exc:
        LOGGER.error("Failed while melting data into long format.")
        LOGGER.exception(exc)
        return None

    # normalize race/sex labels
    try:
        rsi_norm = long_df["Race/Sex Indicator"].astype(str).str.strip().str.lower()
        LOGGER.info("Normalized Race/Sex Indicator labels.")
    except Exception as exc:
        LOGGER.error("Failed while normalizing Race/Sex Indicator labels.")
        LOGGER.exception(exc)
        return None

    # compute MSA totals
    try:
        msa_totals = long_df.groupby(
            id_vars + ["AGEGRP"], as_index=False, observed=True
        )["Population"].sum()
        msa_totals["Race/Sex Indicator"] = "MSA Population"
        LOGGER.info("Computed MSA-level totals. Shape: %s", msa_totals.shape)
    except Exception as exc:
        LOGGER.error("Failed computing MSA totals.")
        LOGGER.exception(exc)
        return None

    # compute gender totals
    try:
        male_mask = rsi_norm.str.endswith(" male")
        female_mask = rsi_norm.str.endswith(" female")

        total_male = (
            long_df.loc[male_mask]
            .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
            .sum()
        )
        total_male["Race/Sex Indicator"] = "Total male"

        total_female = (
            long_df.loc[female_mask]
            .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
            .sum()
        )
        total_female["Race/Sex Indicator"] = "Total female"

        LOGGER.info(
            "Computed male totals shape=%s and female totals shape=%s",
            total_male.shape,
            total_female.shape,
        )
    except Exception as exc:
        LOGGER.error("Failed computing gender totals (male/female).")
        LOGGER.exception(exc)
        return None

    # append computed categories
    try:
        long_augmented = pd.concat(
            [long_df, msa_totals, total_male, total_female], ignore_index=True
        )
        LOGGER.info("Augmented long-format dataset. Shape: %s", long_augmented.shape)
    except Exception as exc:
        LOGGER.error("Failed concatenating augmented population categories.")
        LOGGER.exception(exc)
        return None

    # pivot back to wide format
    try:
        pop_1980_wide = long_augmented.pivot_table(
            index=id_vars + ["AGEGRP"],
            columns="Race/Sex Indicator",
            values="Population",
            aggfunc="sum",
        ).reset_index()

        pop_1980_wide.columns.name = None
        LOGGER.info("Pivoted to wide format. Shape: %s", pop_1980_wide.shape)

        if pop_1980_wide.empty:
            LOGGER.warning("Final wide table is empty — check transformations.")
    except Exception as exc:
        LOGGER.error("Failed pivoting population data to wide format.")
        LOGGER.exception(exc)
        return None

    # map AGEGRP to integer codes
    try:
        age_id_map = {name: i for i, name in enumerate(age_groups_with_total)}
        pop_1980_wide["AGEGRP"] = (
            pop_1980_wide["AGEGRP"].map(age_id_map).astype("Int64")
        )
        LOGGER.info("Mapped AGEGRP labels to integers.")
    except Exception as exc:
        LOGGER.error("Failed mapping AGEGRP values.")
        LOGGER.exception(exc)
        return None

    # final column ordering
    try:
        race_cols = [c for c in pop_1980_wide.columns if c not in id_vars + ["AGEGRP"]]
        preferred = [
            c
            for c in ["MSA Population", "Total male", "Total female"]
            if c in race_cols
        ]
        others = [c for c in race_cols if c not in preferred]
        race_cols = preferred + others

        final_pop_1980 = (
            pop_1980_wide.sort_values(id_vars + ["AGEGRP"]).reset_index(drop=True)
        )[id_vars + ["AGEGRP"] + race_cols]

        LOGGER.info(
            "Final 1980 population dataset created. Shape: %s", final_pop_1980.shape
        )
    except Exception as exc:
        LOGGER.error("Failed constructing final output table.")
        LOGGER.exception(exc)
        return None

    LOGGER.info("1980 population transformation pipeline completed successfully.")
    return final_pop_1980


def rename_pop_1980_columns(final_pop_1980: pd.DataFrame) -> pd.DataFrame:
    """Renames columns in the 1980 final population table to match 2022 naming."""
    LOGGER.info("Starting renaming of final_pop_1980 columns to 2022 format.")

    if final_pop_1980 is None or final_pop_1980.empty:
        LOGGER.error("final_pop_1980 is empty or None. Cannot rename columns.")
        return None

    expected_before = [
        "MSA Population",
        "Total male",
        "Total female",
        "Black female",
        "Black male",
        "Other races female",
        "Other races male",
        "White female",
        "White male",
        "Year of Estimate",
    ]

    missing_cols = [c for c in expected_before if c not in final_pop_1980.columns]
    if missing_cols:
        LOGGER.warning(
            "Some expected columns for renaming are missing: %s", missing_cols
        )

    rename_map = {
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
        final_pop_1980_renamed = final_pop_1980.rename(columns=rename_map)
        LOGGER.info(
            "Renamed final_pop_1980 columns. New columns: %s",
            list(final_pop_1980_renamed.columns),
        )
        return final_pop_1980_renamed

    except Exception as exc:
        LOGGER.error("Failed renaming columns in final_pop_1980.")
        LOGGER.exception(exc)
        return None


def make_msa_tables(final_pop_df: pd.DataFrame) -> pd.DataFrame:
    """Builds 1980 MSA-level race/sex proportion tables and logs all steps.

    Returns:
        dict: mapping {msa_title: DataFrame of 2x3 proportions}
    """
    LOGGER.info("Starting construction of 1980 MSA race/sex proportion tables.")

    if final_pop_df is None or final_pop_df.empty:
        LOGGER.error("final_pop_1980 is empty or None. Cannot compute proportions.")
        return {}

    required_cols = {
        "metro_title",
        "TOT_POP",
        "TOT_MALE",
        "TOT_FEMALE",
        "WAC_MALE",
        "BAC_MALE",
        "OTHER_MALE",
        "WAC_FEMALE",
        "BAC_FEMALE",
        "OTHER_FEMALE",
    }

    missing = required_cols - set(final_pop_df.columns)
    if missing:
        LOGGER.error(
            "Missing required columns for proportion calculations: %s", missing
        )
        return {}

    LOGGER.info("Aggregating totals by metro_title.")
    try:
        agg_cols = [
            "TOT_POP",
            "TOT_MALE",
            "TOT_FEMALE",
            "WAC_MALE",
            "BAC_MALE",
            "OTHER_MALE",
            "WAC_FEMALE",
            "BAC_FEMALE",
            "OTHER_FEMALE",
        ]
        msa_totals = final_pop_df.groupby("metro_title", as_index=False)[agg_cols].sum()
        LOGGER.info("Computed MSA totals for %d MSAs.", msa_totals.shape[0])
    except Exception as exc:
        LOGGER.error("Failed during aggregation.")
        LOGGER.exception(exc)
        return {}

    # male proportions
    LOGGER.info("Computing male race proportions.")
    try:
        male_props = msa_totals[
            ["metro_title", "WAC_MALE", "BAC_MALE", "OTHER_MALE", "TOT_MALE"]
        ].copy()

        male_props[["White", "Black", "Other"]] = male_props[
            ["WAC_MALE", "BAC_MALE", "OTHER_MALE"]
        ].div(male_props["TOT_MALE"], axis=0)

        male_props = male_props[["metro_title", "White", "Black", "Other"]]
    except Exception as exc:
        LOGGER.error("Failed computing male proportions.")
        LOGGER.exception(exc)
        return {}

    # female proportions
    LOGGER.info("Computing female race proportions.")
    try:
        female_props = msa_totals[
            ["metro_title", "WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE", "TOT_FEMALE"]
        ].copy()

        female_props[["White", "Black", "Other"]] = female_props[
            ["WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE"]
        ].div(female_props["TOT_FEMALE"], axis=0)

        female_props = female_props[["metro_title", "White", "Black", "Other"]]
    except Exception as exc:
        LOGGER.error("Failed computing female proportions.")
        LOGGER.exception(exc)
        return {}

    # assemble per-MSA tables
    LOGGER.info("Building individual MSA tables (2x3 proportion matrices).")
    msa_tables = {}

    try:
        for msa in msa_totals["metro_title"]:
            male_row = male_props.loc[
                male_props["metro_title"] == msa, ["White", "Black", "Other"]
            ].squeeze()

            female_row = female_props.loc[
                female_props["metro_title"] == msa, ["White", "Black", "Other"]
            ].squeeze()

            table = pd.DataFrame(
                [male_row.to_numpy(), female_row.to_numpy()],
                index=["Male", "Female"],
                columns=["White", "Black", "Other"],
            ).astype(float)

            table = (table * 100).round(2)
            msa_tables[msa] = table

        LOGGER.info("Finished building tables for %d MSAs.", len(msa_tables))

    except Exception as exc:
        LOGGER.error("Error assembling proportion tables.")
        LOGGER.exception(exc)
        return {}

    return msa_tables


def get_pop_2022() -> pd.DataFrame:
    """Returns cleaned 2022 population dataframe

    Loads the 2022 population CSV from raw_data, filters to the correct year,
    drops unused columns, and returns a cleaned dataframe.
    """
    file_path = RAW_DATA_DIR / "pop_2022.csv"
    LOGGER.info("Beginning load of 2022 population data from %s", file_path)

    # load file
    try:
        pop2 = pd.read_csv(file_path, encoding="latin1")
        LOGGER.info("Successfully loaded pop_2022.csv with %d rows.", pop2.shape[0])
    except FileNotFoundError:
        LOGGER.error("pop_2022.csv not found at path: %s", file_path)
        return None
    except Exception as exc:
        LOGGER.error("Failed to read pop_2022.csv.")
        LOGGER.exception(exc)
        return None

    # drop irrelevant columns
    drop_cols = ["MDIV", "LSAD", "SUMLEV"]
    missing = [c for c in drop_cols if c not in pop2.columns]
    if missing:
        LOGGER.warning(
            "Some expected columns not found and cannot be dropped: %s", missing
        )

    try:
        pop2 = pop2.drop(columns=[c for c in drop_cols if c in pop2.columns])
        LOGGER.info("Dropped columns: %s", drop_cols)
    except Exception as exc:
        LOGGER.error("Error dropping unused columns from pop_2022.")
        LOGGER.exception(exc)
        return None

    # filter for 2022
    try:
        before = pop2.shape[0]
        pop2 = pop2.query("`YEAR` == 4")  # 4 = 7/1/2022 estimate
        after = pop2.shape[0]
        LOGGER.info("Filtered YEAR==4 (2022): %d → %d rows", before, after)
    except Exception as exc:
        LOGGER.error("Error filtering pop_2022 for YEAR == 4.")
        LOGGER.exception(exc)
        return None

    # drop YEAR column
    try:
        pop2 = pop2.drop(columns=["YEAR"])
        LOGGER.info("Dropped YEAR column.")
    except KeyError:
        LOGGER.warning("YEAR column not found when attempting to drop it.")
    except Exception as exc:
        LOGGER.error("Unexpected error dropping YEAR column.")
        LOGGER.exception(exc)
        return None

    LOGGER.info(
        "Successfully cleaned 2022 population data: %d rows, %d columns",
        pop2.shape[0],
        pop2.shape[1],
    )

    return pop2


def clean_pop_2022(pop2: pd.DataFrame) -> pd.DataFrame:
    """Turns CBSAs in the original pop_2022 dataset into string

    Returns the same pop_2022 dataframe, but with CBSA entries as strings
    """
    LOGGER.info("Starting pop_2022 cleaning — converting CBSA to 5-digit strings.")

    if "CBSA" not in pop2.columns:
        LOGGER.error("Column 'CBSA' not found in BFI dataframe.")
        return None
    try:
        pop2["CBSA"] = (
            pd.to_numeric(pop2["CBSA"], errors="coerce")
            .astype("Int64")  # allows NA safely
            .astype(str)
            .str.zfill(5)
        )

        LOGGER.info("Successfully cleaned CBSA column to 5-digit strings.")

    except Exception as exc:
        LOGGER.error("Failed while cleaning CBSA in pop_2022 dataset.")
        LOGGER.exception(exc)
        return None

    return pop2


def merge_pop_2022_with_bfi(pop2: pd.DataFrame, bfi_df: pd.DataFrame) -> pd.DataFrame:
    """Only keeps rows with MSAs relevant/matching to those in the original BFI dataset.

    Returns a subset of the original dataframe that matches that requirement
    """
    LOGGER.info("Beginning merge of 2020 population data with BFI MSA information.")

    try:
        before_rows = pop2.shape[0]
        LOGGER.info("msa_pop_2022 has %d rows before merge.", before_rows)

        merged_pop_2022 = pop2.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="CBSA",
            right_on="metro13",
            how="inner",
        ).drop(columns=["CBSA", "NAME"])

        after_rows = merged_pop_2022.shape[0]
        LOGGER.info(
            "Merge complete. Rows: %d → %d (kept %.2f%%).",
            before_rows,
            after_rows,
            100 * after_rows / before_rows if before_rows > 0 else 0,
        )
        return merged_pop_2022

    except KeyError as exc:
        LOGGER.error("KeyError during merge. Expected columns missing: %s", exc)
        LOGGER.error(
            "Available msa_pop_2022 columns: %s", merged_pop_2022.columns.tolist()
        )
        LOGGER.error("Available bfi_df columns: %s", bfi_df.columns.tolist())
        LOGGER.exception(exc)  # stack trace
        raise

    except Exception as exc:
        LOGGER.error("Unexpected error merging 2022 population data with BFI dataset.")
        LOGGER.exception(exc)
        raise


def organize_pop_2022_minimal(merged_pop_2022: pd.DataFrame) -> pd.DataFrame:
    """Restructures merged 2022 population data into MSA totals by race/sex.

    Returns a cleaned dataframe with:
    metro13, metro_title,
    TOT_POP, TOT_MALE, TOT_FEMALE,
    WAC_MALE, WAC_FEMALE,
    BAC_MALE, BAC_FEMALE,
    OTHER_MALE, OTHER_FEMALE
    """
    LOGGER.info("Beginning 2022 minimal-category restructuring.")

    required_base_cols = [
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

    required_other_m = ["IAC_MALE", "AAC_MALE", "NAC_MALE", "H_MALE"]
    required_other_f = ["IAC_FEMALE", "AAC_FEMALE", "NAC_FEMALE", "H_FEMALE"]

    # --- Check required columns ---
    missing_cols = [
        c
        for c in required_base_cols + required_other_m + required_other_f
        if c not in merged_pop_2022.columns
    ]
    if missing_cols:
        LOGGER.error(
            "Missing required columns for 2022 restructuring: %s", missing_cols
        )
        raise KeyError(f"Missing required columns: {missing_cols}")

    # filter AGEGRP == 0
    try:
        before = merged_pop_2022.shape[0]
        min_df_2022 = merged_pop_2022.query("`AGEGRP` == 0").copy()
        after = min_df_2022.shape[0]
        LOGGER.info("Filtered AGEGRP==0: %d → %d rows.", before, after)
    except Exception as exc:
        LOGGER.error("Failed to filter AGEGRP == 0 for 2022 population.")
        LOGGER.exception(exc)
        raise

    # select base columns
    try:
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
        LOGGER.info("Selected base demographic columns for 2022 minimal frame.")
    except Exception as exc:
        LOGGER.error("Error selecting base columns for 2022 minimal frame.")
        LOGGER.exception(exc)
        raise

    # compute OTHER_MALE and OTHER_FEMALE
    try:
        min_df_2022["OTHER_MALE"] = merged_pop_2022[required_other_m].sum(axis=1)
        min_df_2022["OTHER_FEMALE"] = merged_pop_2022[required_other_f].sum(axis=1)
        LOGGER.info("Computed OTHER_MALE and OTHER_FEMALE aggregates.")
    except Exception as exc:
        LOGGER.error("Failed computing OTHER race-sex totals for 2022.")
        LOGGER.exception(exc)
        raise

    LOGGER.info(
        "Successfully created minimal 2022 population dataset with %d rows and %d columns.",
        min_df_2022.shape[0],
        min_df_2022.shape[1],
    )

    return min_df_2022


# # Employment
def get_industry(year: int) -> pd.DataFrame:
    """Loads and cleans {year} industry labor data from labor_{year}.csv.

      - Drops unused columns
      - Pads area_fips to 5-digit FIPS strings

    Returns:
        pd.DataFrame or None if loading fails.
    """
    file_path = RAW_DATA_DIR / f"labor_{year}.csv"
    LOGGER.info(f"Loading {year} industry labor data from %s", file_path)

    # load CSV
    try:
        ind_df = pd.read_csv(file_path)
        LOGGER.info(f"Successfully read labor_{year}.csv with shape %s", ind_df.shape)
    except FileNotFoundError:
        LOGGER.error(f"labor_{year}.csv not found at %s", file_path)
        return None
    except Exception as exc:
        LOGGER.error(f"Failed to read labor_{year}.csv.")
        LOGGER.exception(exc)
        return None

    # drop unnecessary columns
    drop_cols = ["own_code", "industry_code", "qtr", "disclosure_code"]
    existing_drop_cols = [c for c in drop_cols if c in ind_df.columns]
    missing = [c for c in drop_cols if c not in ind_df.columns]

    if missing:
        LOGGER.warning(
            "Some expected columns not found and cannot be dropped: %s", missing
        )

    try:
        ind_df = ind_df.drop(columns=existing_drop_cols)
        LOGGER.info(
            "Dropped columns %s. New shape: %s", existing_drop_cols, ind_df.shape
        )
    except Exception as exc:
        LOGGER.error(f"Failed to drop columns from labor_{year} dataframe.")
        LOGGER.exception(exc)
        return None

    # pad area_fips to 5-digit strings
    if "area_fips" not in ind_df.columns:
        LOGGER.error(f"Column 'area_fips' not found in labor_{year} data.")
        return None

    try:
        # convert to numeric and drop non-numeric codes like 'US000'
        area_numeric = pd.to_numeric(ind_df["area_fips"], errors="coerce")

        bad_codes = ind_df.loc[area_numeric.isna(), "area_fips"].unique()
        if len(bad_codes) > 0:
            LOGGER.warning(
                "Dropping %d rows with non-numeric area_fips codes (e.g. %s) "
                "from labor_%s data.",
                area_numeric.isna().sum(),
                bad_codes[:5],
                year,
            )

        ind_df = ind_df.loc[area_numeric.notna()].copy()
        ind_df["area_fips"] = (
            area_numeric[area_numeric.notna()].astype("Int64").astype(str).str.zfill(5)
        )

        LOGGER.info(
            "Padded area_fips to 5-digit strings after dropping non-numeric codes."
        )
    except Exception as exc:
        LOGGER.error("Failed to clean/format area_fips in labor_%s.", year)
        LOGGER.exception(exc)
        return None

    LOGGER.info(f"Finished processing labor_{year}.csv. Final shape: %s", ind_df.shape)
    return ind_df


def combine_industries() -> pd.DataFrame:
    """Combines 1980 and 2022 industry labor datasets

    Loads, combines them, and logs each major step.
    """
    LOGGER.info("Combining 1980 and 2022 industry datasets...")

    ind_1980 = get_industry(1980)
    if ind_1980 is None:
        LOGGER.error("Failed to load 1980 industry data.")
        return None
    LOGGER.info("Loaded 1980 industry dataset with %d rows.", len(ind_1980))

    ind_2022 = get_industry(2022)
    if ind_2022 is None:
        LOGGER.error("Failed to load 2022 industry data.")
        return None
    LOGGER.info("Loaded 2022 industry dataset with %d rows.", len(ind_2022))

    try:
        all_ind = pd.concat([ind_1980, ind_2022], ignore_index=True)
        LOGGER.info(
            "Successfully combined industry datasets. Final row count: %d",
            len(all_ind),
        )
    except Exception as exc:
        LOGGER.error("Failed to concatenate 1980 and 2022 industry datasets.")
        LOGGER.exception(exc)
        return None

    return all_ind


def merge_industry_with_msa(
    all_ind: pd.DataFrame, msa_county: pd.DataFrame, bfi_df: pd.DataFrame
) -> pd.DataFrame:
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
    required_cols_ind = {"area_fips"}
    required_cols_cross = {"cbsacode", "fips", "cbsatitle"}
    required_cols_bfi = {"metro13", "metro_title"}

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
        msa_all_ind = all_ind.merge(
            msa_county[["cbsacode", "fips", "cbsatitle"]],
            left_on="area_fips",
            right_on="fips",
            how="inner",
        ).drop(columns=["area_fips"])

        LOGGER.info(
            "Merge 1 complete: industry ↔ MSA crosswalk. Rows before: %d → after: %d",
            len(all_ind),
            len(msa_all_ind),
        )

    except Exception as exc:
        LOGGER.error("Failed merging industry data with MSA crosswalk")
        LOGGER.exception(exc)
        return None

    # second merge: keep only MSAs in BFI dataset
    try:
        merged_all_ind = msa_all_ind.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="cbsacode",
            right_on="metro13",
            how="inner",
        ).drop(columns=["cbsacode", "cbsatitle", "fips", "industry_title"])

        LOGGER.info(
            "Merge 2 complete: keeping only BFI MSAs. Rows before: %d → after: %d",
            len(msa_all_ind),
            len(merged_all_ind),
        )
    except Exception as exc:
        LOGGER.error("Failed merging MSA industry data with BFI dataset")
        LOGGER.exception(exc)
        return None

    # keep only Total Covered
    try:
        before = len(merged_all_ind)
        merged_all_ind = merged_all_ind.query('`own_title` == "Total Covered"')
        LOGGER.info(
            'Filtered rows where own_title == "Total Covered": %d → %d',
            before,
            len(merged_all_ind),
        )
    except Exception as exc:
        LOGGER.error("Failed filtering to own_title == 'Total Covered'")
        LOGGER.exception(exc)
        return None

    LOGGER.info("Successfully completed industry–MSA merging pipeline.")
    return merged_all_ind


def build_msa_industry_tables(merged_all_ind: pd.DataFrame) -> None:
    """Aggregates industry data by MSA and year, computes summary tables.

    Summary tables contain: (establishments, employment, wages, weekly wages),
    and calculates percent changes across years when available.

    Parameters:
        merged_all_ind (pd.DataFrame): Cleaned industry dataset with MSA codes.

    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping metro_title → summary table.
    """
    LOGGER.info("Starting MSA industry table construction...")

    required_cols = {
        "metro13",
        "metro_title",
        "year",
        "annual_avg_estabs_count",
        "annual_avg_emplvl",
        "total_annual_wages",
        "annual_avg_wkly_wage",
    }

    # validate columns
    if not required_cols.issubset(merged_all_ind.columns):
        missing = required_cols - set(merged_all_ind.columns)
        LOGGER.error("Missing required columns for aggregation: %s", missing)
        return {}

    # aggregate by MSA + year
    try:
        LOGGER.info("Aggregating industry metrics by MSA and year...")

        agg_df = merged_all_ind.groupby(
            ["metro13", "metro_title", "year"], as_index=False
        ).agg(
            {
                "annual_avg_estabs_count": "sum",
                "annual_avg_emplvl": "sum",
                "total_annual_wages": "sum",
                "annual_avg_wkly_wage": "mean",
            }
        )

        LOGGER.info("Aggregation complete. Aggregated rows: %d", len(agg_df))

    except Exception as exc:
        LOGGER.error("Failed during MSA industry aggregation.")
        LOGGER.exception(exc)
        return {}

    # build tables for each MSA
    msa_tables = {}

    try:
        LOGGER.info("Constructing per-MSA summary tables...")

        for msa, sub in agg_df.groupby("metro_title"):
            LOGGER.debug("Processing MSA: %s (rows: %d)", msa, len(sub))

            table = sub.set_index("year")[
                [
                    "annual_avg_estabs_count",
                    "annual_avg_emplvl",
                    "total_annual_wages",
                    "annual_avg_wkly_wage",
                ]
            ].T

            table.index = [
                "Average Establishments",
                "Average Employment (Jobs)",
                "Total Annual Wages ($)",
                "Average Weekly Wage ($)",
            ]

            # if two or more years exist, compute percent change
            years = sorted(sub["year"].unique())
            if len(years) > 1:
                y0, y1 = years[0], years[-1]
                LOGGER.debug("Computing %% change for %s: %d → %d", msa, y0, y1)

                table["% Change"] = (table[y1] - table[y0]) / table[y0] * 100

            msa_tables[msa] = table.round(2)

        LOGGER.info("Successfully built %d MSA tables.", len(msa_tables))

    except Exception as exc:
        LOGGER.error("Error occurred while constructing MSA tables.")
        LOGGER.exception(exc)
        return {}

    return msa_tables


def build_bfi_pop_labor(
    bfi_df: pd.DataFrame,
    final_pop_1980: pd.DataFrame,
    min_df_2022: pd.DataFrame,
    merged_all_ind: pd.DataFrame,
    output_path: Path | str | None = None,
) -> pd.DataFrame:
    """Builds the combined BFI + population + labor dataset for 1980 and 2022.

    Steps:
      1. Duplicate BFI dataframe for 1980 and 2022 and stack.
      2. Combine 1980 and 2022 population data (AGEGRP 0 for 1980, minimal 2022).
      3. Merge BFI with population and industry metrics.
      4. Rename selected columns to clean variable names.
      5. Optionally write final dataframe to CSV.

    Returns:
        new_bfi_df (pd.DataFrame): final merged dataset.
    """
    LOGGER.info("Starting build of combined BFI + population + labor dataset.")

    # 1. Build BFI years frame
    try:
        bfi_df1980 = bfi_df.copy()
        bfi_df1980["year"] = 1980

        bfi_df2022 = bfi_df.copy()
        bfi_df2022["year"] = 2022

        bfi_yrs = pd.concat([bfi_df1980, bfi_df2022], ignore_index=True)
        LOGGER.info("Constructed BFI years dataframe with %d rows.", len(bfi_yrs))
    except Exception as exc:
        LOGGER.error("Failed while constructing BFI years dataframe.")
        LOGGER.exception(exc)
        return None

    # 2. Combine population dataframes
    try:
        # Keep only AGEGRP 0 for 1980 total population
        tot_final_pop_1980 = final_pop_1980.query("`AGEGRP` == 0").copy()
        LOGGER.info(
            "Filtered 1980 population to AGEGRP==0: %d rows.",
            len(tot_final_pop_1980),
        )

        min_df_2022 = min_df_2022.copy()
        min_df_2022["year"] = 2022

        pop_df = pd.concat(
            [tot_final_pop_1980, min_df_2022],
            ignore_index=True,
            axis=0,
        ).drop(columns=["AGEGRP"], errors="ignore")

        LOGGER.info(
            "Combined 1980 and 2022 population data into pop_df with shape %s.",
            pop_df.shape,
        )
    except Exception as exc:
        LOGGER.error("Failed while combining population dataframes.")
        LOGGER.exception(exc)
        return None

    # 3. Merge BFI with population and industry data
    try:
        LOGGER.info("Merging BFI with population data...")
        new_bfi_df = bfi_yrs.merge(
            pop_df.drop(columns="metro_title", errors="ignore"),
            on=["metro13", "year"],
            how="left",
        )

        LOGGER.info(
            "After population merge, shape is %s (rows: %d).",
            new_bfi_df.shape,
            len(new_bfi_df),
        )

        LOGGER.info("Merging BFI+population with industry data...")
        new_bfi_df = new_bfi_df.merge(
            merged_all_ind[
                [
                    "metro13",
                    "year",
                    "annual_avg_estabs_count",
                    "annual_avg_emplvl",
                    "total_annual_wages",
                    "annual_avg_wkly_wage",
                ]
            ],
            on=["metro13", "year"],
            how="left",
        )
        LOGGER.info(
            "After industry merge, final shape is %s (rows: %d).",
            new_bfi_df.shape,
            len(new_bfi_df),
        )
    except KeyError as exc:
        LOGGER.error("KeyError during merge: %s", exc)
        LOGGER.error("Columns in bfi_yrs: %s", bfi_yrs.columns.tolist())
        LOGGER.error("Columns in pop_df: %s", pop_df.columns.tolist())
        LOGGER.error("Columns in merged_all_ind: %s", merged_all_ind.columns.tolist())
        LOGGER.exception(exc)
        return None
    except Exception as exc:
        LOGGER.error("Unexpected error during BFI/pop/industry merging.")
        LOGGER.exception(exc)
        return None

    # rename columns to nicer names (if present)
    try:
        rename_map = {
            "race/sex indicator": "race/sex_indicator",
            "total population": "total_population",
        }
        existing_rename_keys = [c for c in rename_map if c in new_bfi_df.columns]
        if not existing_rename_keys:
            LOGGER.warning(
                "No matching columns found for renaming: %s",
                list(rename_map.keys()),
            )

        new_bfi_df = new_bfi_df.rename(
            columns={k: rename_map[k] for k in existing_rename_keys}
        )
        LOGGER.info("Renamed columns where applicable: %s", existing_rename_keys)
    except Exception as exc:
        LOGGER.error("Failed renaming columns in new_bfi_df.")
        LOGGER.exception(exc)
        return None

    # optionally write to CSV
    if output_path is not None:
        try:
            output_path = Path(output_path)
            new_bfi_df.to_csv(output_path, index=False)
            LOGGER.info("Wrote combined BFI dataset to %s", output_path)
        except Exception as exc:
            LOGGER.error(
                "Failed writing combined BFI dataset to CSV at %s", output_path
            )
            LOGGER.exception(exc)
            # still return the dataframe even if save fails

    LOGGER.info("Successfully built combined BFI + population + labor dataset.")
    return new_bfi_df


def main() -> dict[str, Any]:
    """Combines all functions to produce merged_bfi.csv.

    merged_bfi.csv contains all columns and rows used from
    1980 and 2022 population and industry datasets

    Returns dictionaries for 1980 population proportions,
    2022 population proportions, and 1980 vs 2022 industry changes
    """
    # ---- 1. (Optional) Download raw data if not already present ----
    # Comment these out if you already have the CSVs in RAW_DATA_DIR.
    get_census_pop()
    get_ubls_labor()
    get_uber_county_cbsa_crosswalk()

    # ---- 2. Load and clean BFI ----
    bfi_df = get_bfi()
    if bfi_df is None:
        LOGGER.error("BFI data could not be loaded. Aborting.")
        return

    bfi_df = clean_bfi(bfi_df)
    if bfi_df is None:
        LOGGER.error("BFI data could not be cleaned. Aborting.")
        return

    # ---- 3. 1980 population pipeline ----
    raw_pop_1980 = get_pop_1980()
    if raw_pop_1980 is None:
        LOGGER.error("Raw 1980 population data could not be loaded. Aborting.")
        return

    pop_1980 = clean_pop_1980(raw_pop_1980)
    if pop_1980 is None:
        LOGGER.error("1980 population data could not be cleaned. Aborting.")
        return

    # CBSA crosswalk
    raw_msa_county = get_cbsa_county_crosswalk()
    if raw_msa_county is None:
        LOGGER.error("CBSA crosswalk could not be loaded. Aborting.")
        return

    msa_county = clean_cbsa_county_crosswalk(raw_msa_county)
    if msa_county is None:
        LOGGER.error("CBSA crosswalk could not be cleaned. Aborting.")
        return

    # 1980 pop + crosswalk + BFI
    msa_pop_1980 = merge_pop_1980_with_cbsa(pop_1980, msa_county)
    if msa_pop_1980 is None:
        LOGGER.error("Failed merging 1980 population with CBSA crosswalk. Aborting.")
        return

    merged_pop_1980 = merge_pop_1980_with_bfi(msa_pop_1980, bfi_df)
    if merged_pop_1980 is None:
        LOGGER.error("Failed merging 1980 population with BFI dataset. Aborting.")
        return

    pop_1980_agg = aggregate_pop_1980(merged_pop_1980)
    if pop_1980_agg is None:
        LOGGER.error("Failed aggregating 1980 population data. Aborting.")
        return

    final_pop_1980 = transform_pop_1980_to_final(pop_1980_agg)
    if final_pop_1980 is None:
        LOGGER.error("Failed transforming 1980 population data. Aborting.")
        return

    final_pop_1980 = rename_pop_1980_columns(final_pop_1980)
    if final_pop_1980 is None:
        LOGGER.error("Failed renaming 1980 population columns. Aborting.")
        return

    # ---- 4. 2022 population pipeline ----
    pop_2022 = get_pop_2022()
    if pop_2022 is None:
        LOGGER.error("2022 population data could not be loaded. Aborting.")
        return

    pop_2022 = clean_pop_2022(pop_2022)
    if pop_2022 is None:
        LOGGER.error("2022 population data could not be cleaned. Aborting.")
        return

    merged_pop_2022 = merge_pop_2022_with_bfi(pop_2022, bfi_df)
    if merged_pop_2022 is None:
        LOGGER.error("Failed merging 2022 population with BFI dataset. Aborting.")
        return

    min_df_2022 = organize_pop_2022_minimal(merged_pop_2022)

    # ---- 5. Industry pipeline ----
    all_ind = combine_industries()
    if all_ind is None:
        LOGGER.error("Industry datasets could not be combined. Aborting.")
        return

    merged_all_ind = merge_industry_with_msa(all_ind, msa_county, bfi_df)
    if merged_all_ind is None:
        LOGGER.error("Failed merging industry data with MSAs. Aborting.")
        return

    # ---- 6. Build final merged BFI dataset and write CSV ----
    output_path = DATA_DIR / "merged_bfi.csv"
    new_bfi_df = build_bfi_pop_labor(
        bfi_df=bfi_df,
        final_pop_1980=final_pop_1980,
        min_df_2022=min_df_2022,
        merged_all_ind=merged_all_ind,
        output_path=output_path,
    )

    if new_bfi_df is None:
        LOGGER.error("Failed to build final BFI + pop + labor dataset.")
        return

    LOGGER.info("Pipeline complete. Final dataset saved to %s", output_path)

    # build tables
    pop_1980_table = make_msa_tables(final_pop_1980)
    pop_2022_table = make_msa_tables(min_df_2022)
    labor_table = build_msa_industry_tables(merged_all_ind)

    return pop_1980_table, pop_2022_table, labor_table


if __name__ == "__main__":
    pop_1980_table, pop_2022_table, labor_table = main()
