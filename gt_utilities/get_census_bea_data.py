"""Supplementary analysis using 1980 and 2022 population and labor data.

This file first obtains raw data and saves them in /data/raw_data and then
cleans and retrieves them, reformatting them into tables
"""

import io
import logging
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests
from requests.exceptions import ReadTimeout, RequestException

# Initialize Paths
DATA_DIR = Path(os.environ.get("DATA_DIR", "data")).resolve()
RAW_DATA_DIR = DATA_DIR / "raw_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Logger
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
        try:
            LOGGER.info("Requesting %s Census data...", year)
            r = requests.get(url, timeout=30)
            r.raise_for_status()
        except ReadTimeout as exc:
            LOGGER.error(
                "Timed out while downloading %s census data from %s", year, url
            )
            LOGGER.exception(exc)
            continue
        except RequestException as exc:
            LOGGER.error("Failed to download %s population data from %s", year, url)
            LOGGER.exception(exc)
            return

        output_file = RAW_DATA_DIR / f"pop_{year}.csv"

        try:
            with output_file.open("wb") as f:
                f.write(r.content)
            LOGGER.info("Saved pop_%s.csv to %s", year, output_file.resolve())
        except OSError as exc:
            LOGGER.error("Failed to write output file: %s", output_file)
            LOGGER.exception(exc)
            return
    return


def get_ubls_labor(
    zip_urls: dict[str, str] = UBLA_LABOR_DATA_ZIP_URLS_AND_RAW_PATHS,
) -> None:
    """Unzips folder containing 1980 employment data for all industries.

    From US Bureau of Labor Statistics at:
    https://www.bls.gov/cew/downloadable-data-files.htm
    """
    for zip_url, path in zip_urls.items():
        year = "1980" if "1980" in zip_url else "2022"

        try:
            LOGGER.info("Requesting %s Labor data (ZIP)...", year)
            r = requests.get(zip_url, timeout=30)
            r.raise_for_status()
        except RequestException as exc:
            LOGGER.error(
                "Failed to download %s labor data zipfile from %s", year, zip_url
            )
            LOGGER.exception(exc)
            return

        output_file = RAW_DATA_DIR / f"labor_{year}.csv"

        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                # Check if file exists in zip before extracting
                if path not in z.namelist():
                    LOGGER.error("File %s not found in ZIP archive %s", path, zip_url)
                    continue

                with z.open(path) as source, output_file.open("wb") as target:
                    target.write(source.read())

            LOGGER.info(
                "Saved labor_%s.csv to %s", year, output_file.resolve()
            )  # Fixed format

        except zipfile.BadZipFile:
            LOGGER.error("The downloaded file is not a valid ZIP archive.")
            return
        except OSError as exc:
            LOGGER.error("Failed to write output file: %s", output_file)
            LOGGER.exception(exc)
            return
    return


def get_uber_county_cbsa_crosswalk(
    url: str = NBER_COUNTY_CBSA_CROSSWALK_URL,
) -> None:
    """Saves csv containing 2013 cbsa to county crosswalk

    From National Bureau of Economic Research at:
    https://data.nber.org/cbsa-msa-fips-ssa-county-crosswalk/2013/
    """
    try:
        LOGGER.info("Requesting NBER crosswalk data...")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except RequestException:
        LOGGER.error("Failed to download crosswalk data from %s", url, exc_info=True)
        return

    output_file = RAW_DATA_DIR / "cbsatocountycrosswalk.csv"

    try:
        with output_file.open("wb") as f:
            f.write(r.content)
        LOGGER.info("Saved cbsatocountycrosswalk.csv to %s", output_file.resolve())
    except OSError:
        LOGGER.error("Failed to write output file: %s", output_file, exc_info=True)
        return


def get_pop_1980() -> pd.DataFrame | None:
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
        # Check logic: drop row 0 if it's empty/informational
        if not pop.empty:
            pop = pop.drop(0)

        LOGGER.info("Successfully read pop_1980.csv. Shape: %s", pop.shape)
        return pop

    except Exception as exc:
        LOGGER.error("Error reading pop_1980.csv: %s", exc, exc_info=True)
        return None


def get_bfi() -> pd.DataFrame | None:
    """Retrieves original bfi csv from data folder.

    Returns the csv as a dataframe.
    """
    csv_path = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
    LOGGER.info("Loading BFI data from %s", csv_path)

    try:
        bfi_df = pd.read_csv(csv_path)
        LOGGER.info("Loaded BFI csv. Shape: %s", bfi_df.shape)
        return bfi_df
    except Exception as exc:
        LOGGER.error("Error reading BFI csv: %s", exc, exc_info=True)
        return None


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
    required_cols = ["Year of Estimate", "FIPS State and County Codes"]
    for col in required_cols:
        if col not in pop.columns:
            LOGGER.error("Missing required column '%s' in population data.", col)
            return None

    try:
        # Filter 1980
        pop_1980 = pop.query(
            "`Year of Estimate` == 1980"
        ).copy()  # Use .copy() to avoid SettingWithCopy warning

        # Calculate Total Population (Summing cols 3 onwards)
        cols_to_sum = list(pop_1980.columns)[3:]
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


def get_cbsa_county_crosswalk() -> pd.DataFrame | None:
    """Retrieves the cbsa to county crosswalk csv."""
    csv_path = RAW_DATA_DIR / "cbsatocountycrosswalk.csv"
    LOGGER.info("Loading crosswalk from %s", csv_path)

    try:
        msa_county = pd.read_csv(csv_path, encoding="latin1")
        LOGGER.info("Loaded crosswalk. Shape: %s", msa_county.shape)
        return msa_county
    except Exception as exc:
        LOGGER.error("Error reading crosswalk: %s", exc, exc_info=True)
        return None


def clean_cbsa_county_crosswalk(msa_county: pd.DataFrame) -> pd.DataFrame | None:
    """Creates FIPS codes and cleans CBSA codes."""
    LOGGER.info("Cleaning crosswalk data...")

    required = ["fipsstatecode", "fipscountycode", "cbsacode"]
    if not all(col in msa_county.columns for col in required):
        LOGGER.error("Missing columns in crosswalk. Required: %s", required)
        return None

    try:
        # Create full FIPS
        msa_county["fips"] = pd.to_numeric(
            msa_county["fipsstatecode"], errors="coerce"
        ).astype("Int64").astype(str).str.zfill(2) + pd.to_numeric(
            msa_county["fipscountycode"], errors="coerce"
        ).astype("Int64").astype(str).str.zfill(3)

        # Clean CBSA
        msa_county["cbsacode"] = (
            pd.to_numeric(msa_county["cbsacode"], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(5)
        )
        LOGGER.info("Crosswalk cleaned. Added 'fips' and formatted 'cbsacode'.")
        return msa_county
    except Exception as exc:
        LOGGER.error("Error cleaning crosswalk: %s", exc, exc_info=True)
        return None


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
        merged = pop_1980.merge(
            msa_county[["cbsacode", "fips", "cbsatitle"]],
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
        merged_pop_1980 = msa_pop_1980.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="cbsacode",
            right_on="metro13",
            how="inner",
        ).drop(columns=["cbsacode", "cbsatitle"])

        LOGGER.info(
            "Filtered 1980 data to %d rows matching BFI MSAs.", len(merged_pop_1980)
        )
        return merged_pop_1980
    except Exception as exc:
        LOGGER.error("Error merging with BFI: %s", exc, exc_info=True)
        return None


def aggregate_pop_1980(merged_pop_1980: pd.DataFrame) -> pd.DataFrame | None:
    """Aggregates 1980 population data to the MSA level.

    Sums across all counties (FIPS) for each Race/Sex category.

    Returns:
        Aggregated dataframe or None if the aggregation fails.
    """
    LOGGER.info("Aggregating 1980 Pop to MSA level...")

    group_cols = ["Year of Estimate", "Race/Sex Indicator", "metro13", "metro_title"]

    try:
        pop_1980_agg = (
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
        age_groups_with_total = ["Total Population"] + pop_1980_agg.columns[
            3:-4
        ].to_list()
        id_vars = ["Year of Estimate", "metro13", "metro_title"]

        # Melt to long
        long_df = pop_1980_agg.melt(
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
        msa_totals = long_df.groupby(
            id_vars + ["AGEGRP"], as_index=False, observed=True
        )["Population"].sum()
        msa_totals["Race/Sex Indicator"] = "MSA Population"

        # 2. Gender Totals
        total_male = (
            long_df[long_df["Race/Sex Indicator"].str.endswith(" male")]
            .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
            .sum()
        )
        total_male["Race/Sex Indicator"] = "Total male"

        total_female = (
            long_df[long_df["Race/Sex Indicator"].str.endswith(" female")]
            .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
            .sum()
        )
        total_female["Race/Sex Indicator"] = "Total female"

        # Combine
        long_augmented = pd.concat(
            [long_df, msa_totals, total_male, total_female], ignore_index=True
        )

        # Pivot to Wide
        pop_1980_wide = long_augmented.pivot_table(
            index=id_vars + ["AGEGRP"],
            columns="Race/Sex Indicator",
            values="Population",
            aggfunc="sum",
        ).reset_index()
        pop_1980_wide.columns.name = None

        # Map AGEGRP to IDs
        age_id_map = {name: i for i, name in enumerate(age_groups_with_total)}
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
        LOGGER.info("Renamed 1980 columns to 2022 standard.")
        return final_pop_1980_renamed
    except Exception as exc:
        LOGGER.error("Error renaming columns: %s", exc, exc_info=True)
        return None


def make_msa_tables(final_pop_df: pd.DataFrame) -> dict:
    """Builds 1980 MSA-level race/sex proportion tables and logs all steps.

    Returns:
        dict: mapping {msa_title: DataFrame of 2x3 proportions}
    """
    LOGGER.info("Building MSA proportion tables...")

    msa_tables = {}

    try:
        # Aggregate totals by MSA
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

        # Ensure cols exist
        if not all(col in final_pop_df.columns for col in agg_cols + ["metro_title"]):
            LOGGER.error("Missing columns required for proportion tables.")
            return {}

        msa_totals = final_pop_df.groupby("metro_title", as_index=False)[agg_cols].sum()

        for _, row in msa_totals.iterrows():
            msa = row["metro_title"]

            # Avoid Division by Zero
            t_male = row["TOT_MALE"] if row["TOT_MALE"] > 0 else 1
            t_female = row["TOT_FEMALE"] if row["TOT_FEMALE"] > 0 else 1

            male_stats = [
                row["WAC_MALE"] / t_male,
                row["BAC_MALE"] / t_male,
                row["OTHER_MALE"] / t_male,
            ]
            female_stats = [
                row["WAC_FEMALE"] / t_female,
                row["BAC_FEMALE"] / t_female,
                row["OTHER_FEMALE"] / t_female,
            ]

            table = pd.DataFrame(
                [male_stats, female_stats],
                index=["Male", "Female"],
                columns=["White", "Black", "Other"],
            ).astype(float)

            msa_tables[msa] = (table * 100).round(2)

        LOGGER.info("Generated proportion tables for %d MSAs.", len(msa_tables))
        return msa_tables

    except Exception as exc:
        LOGGER.error("Error building MSA tables: %s", exc, exc_info=True)
        return {}


def get_pop_2022() -> pd.DataFrame | None:
    """Returns cleaned 2022 population dataframe.

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
        LOGGER.error("Failed to read pop_2022.csv: %s", exc, exc_info=True)
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
    except Exception:
        LOGGER.error("Error dropping unused columns from pop_2022.", exc_info=True)
        return None

    # filter for 2022
    try:
        before = pop2.shape[0]
        # Querying for YEAR == 4 (2022 estimate)
        if "YEAR" in pop2.columns:
            pop2 = pop2.query("`YEAR` == 4").copy()
            after = pop2.shape[0]
            LOGGER.info("Filtered YEAR==4 (2022): %d -> %d rows", before, after)
        else:
            LOGGER.warning(
                "'YEAR' column missing. Assuming data is already filtered for 2022."
            )
    except Exception:
        LOGGER.error("Error filtering pop_2022 for YEAR == 4.", exc_info=True)
        return None

    # drop YEAR column
    try:
        if "YEAR" in pop2.columns:
            pop2 = pop2.drop(columns=["YEAR"])
            LOGGER.info("Dropped YEAR column.")
    except Exception:
        LOGGER.error("Unexpected error dropping YEAR column.", exc_info=True)
        return None

    LOGGER.info(
        "Successfully cleaned 2022 population data: %d rows, %d columns",
        pop2.shape[0],
        pop2.shape[1],
    )

    return pop2


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


def merge_pop_2022_with_bfi(
    pop2: pd.DataFrame, bfi_df: pd.DataFrame
) -> pd.DataFrame | None:
    """Only keeps rows with MSAs relevant/matching to those in the original BFI dataset."""
    LOGGER.info("Beginning merge of 2022 population data with BFI MSA information.")

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
        return None

    try:
        # filter AGEGRP == 0 (Total Age)
        before = merged_pop_2022.shape[0]
        min_df_2022 = merged_pop_2022.query("`AGEGRP` == 0").copy()
        after = min_df_2022.shape[0]
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


# # Employment
def get_industry(year: int) -> pd.DataFrame | None:
    """Loads and cleans {year} industry labor data from labor_{year}.csv.

      - Drops unused columns
      - Pads area_fips to 5-digit FIPS strings

    Returns:
        pd.DataFrame or None if loading fails.
    """
    file_path = RAW_DATA_DIR / f"labor_{year}.csv"
    LOGGER.info("Loading %s industry labor data from %s", year, file_path)

    # load CSV
    try:
        ind_df = pd.read_csv(file_path)
        LOGGER.info("Successfully read labor_%s.csv with shape %s", year, ind_df.shape)
    except FileNotFoundError:
        LOGGER.error("labor_%s.csv not found at %s", year, file_path)
        return None
    except Exception as exc:
        LOGGER.error("Failed to read labor_%s.csv: %s", year, exc, exc_info=True)
        return None

    # drop unnecessary columns
    drop_cols = ["own_code", "industry_code", "qtr", "disclosure_code"]
    existing_drop_cols = [c for c in drop_cols if c in ind_df.columns]

    try:
        ind_df = ind_df.drop(columns=existing_drop_cols)
        LOGGER.info(
            "Dropped columns %s. New shape: %s", existing_drop_cols, ind_df.shape
        )
    except Exception:
        LOGGER.error("Failed to drop columns from labor_%s.", year, exc_info=True)
        return None

    # pad area_fips to 5-digit strings
    if "area_fips" not in ind_df.columns:
        LOGGER.error("Column 'area_fips' not found in labor_%s data.", year)
        return None

    try:
        # convert to numeric and drop non-numeric codes like 'US000'
        area_numeric = pd.to_numeric(ind_df["area_fips"], errors="coerce")

        bad_codes = ind_df.loc[area_numeric.isna(), "area_fips"].unique()
        if len(bad_codes) > 0:
            LOGGER.warning(
                "Dropping %d rows with non-numeric area_fips in %s data (e.g. %s)",
                area_numeric.isna().sum(),
                year,
                bad_codes[:5],
            )

        ind_df = ind_df.loc[area_numeric.notna()].copy()
        ind_df["area_fips"] = (
            area_numeric[area_numeric.notna()].astype("Int64").astype(str).str.zfill(5)
        )

        LOGGER.info("Padded area_fips to 5-digit strings.")
        return ind_df

    except Exception:
        LOGGER.error(
            "Failed to clean/format area_fips in labor_%s.", year, exc_info=True
        )
        return None


def combine_industries() -> pd.DataFrame | None:
    """Combines 1980 and 2022 industry labor datasets."""
    LOGGER.info("Combining 1980 and 2022 industry datasets...")

    ind_1980 = get_industry(1980)
    if ind_1980 is None:
        LOGGER.error("Failed to load 1980 industry data.")
        return None

    ind_2022 = get_industry(2022)
    if ind_2022 is None:
        LOGGER.error("Failed to load 2022 industry data.")
        return None

    try:
        all_ind = pd.concat([ind_1980, ind_2022], ignore_index=True)
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
            "Merge 1 (Ind <-> MSA Crosswalk) complete. Rows: %d -> %d",
            len(all_ind),
            len(msa_all_ind),
        )
    except Exception:
        LOGGER.error("Failed merging industry data with MSA crosswalk", exc_info=True)
        return None

    # second merge: keep only MSAs in BFI dataset
    try:
        merged_all_ind = msa_all_ind.merge(
            bfi_df[["metro13", "metro_title"]],
            left_on="cbsacode",
            right_on="metro13",
            how="inner",
        ).drop(
            columns=["cbsacode", "cbsatitle", "fips", "industry_title"], errors="ignore"
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
        before = len(merged_all_ind)
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


def build_msa_industry_tables(merged_all_ind: pd.DataFrame) -> dict:
    """Aggregates industry data by MSA and year, computes summary tables.

    Summary tables contain: (establishments, employment, wages, weekly wages),
    and calculates percent changes across years when available.

    Parameters:
        merged_all_ind (pd.DataFrame): Cleaned industry dataset with MSA codes.

    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping metro_title → summary table.
    """
    LOGGER.info("Starting MSA industry table construction...")

    msa_tables = {}

    required_cols = [
        "metro13",
        "metro_title",
        "year",
        "annual_avg_estabs_count",
        "annual_avg_emplvl",
        "total_annual_wages",
        "annual_avg_wkly_wage",
    ]

    # Check if cols exist
    missing = [c for c in required_cols if c not in merged_all_ind.columns]
    if missing:
        LOGGER.error("Missing required columns for aggregation: %s", missing)
        return {}

    # aggregate by MSA + year
    try:
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

        # build tables for each MSA
        for msa, sub in agg_df.groupby("metro_title"):
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
                table["% Change"] = (table[y1] - table[y0]) / table[y0] * 100

            msa_tables[msa] = table.round(2)

        LOGGER.info("Successfully built %d MSA tables.", len(msa_tables))
        return msa_tables

    except Exception:
        LOGGER.error("Error occurred while constructing MSA tables.", exc_info=True)
        return {}


def build_bfi_pop_labor(
    bfi_df: pd.DataFrame,
    final_pop_1980: pd.DataFrame,
    min_df_2022: pd.DataFrame,
    merged_all_ind: pd.DataFrame,
    output_path: Path | None = None,
) -> pd.DataFrame | None:
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
        LOGGER.info("Constructed BFI years dataframe. Rows: %d", len(bfi_yrs))
    except Exception:
        LOGGER.error("Failed while constructing BFI years dataframe.", exc_info=True)
        return None

    # 2. Combine population dataframes
    try:
        # Keep only AGEGRP 0 for 1980 total population
        if "AGEGRP" in final_pop_1980.columns:
            tot_final_pop_1980 = final_pop_1980.query("`AGEGRP` == 0").copy()
        else:
            tot_final_pop_1980 = final_pop_1980.copy()
            LOGGER.warning("AGEGRP not found in 1980 pop, skipping filter.")

        min_df_2022_copy = min_df_2022.copy()
        min_df_2022_copy["year"] = 2022

        pop_df = pd.concat(
            [tot_final_pop_1980, min_df_2022_copy],
            ignore_index=True,
            axis=0,
        ).drop(columns=["AGEGRP"], errors="ignore")

        LOGGER.info("Combined 1980 and 2022 population data. Shape: %s", pop_df.shape)
    except Exception:
        LOGGER.error("Failed while combining population dataframes.", exc_info=True)
        return None

    # 3. Merge BFI with population and industry data
    try:
        LOGGER.info("Merging BFI with population data...")
        new_bfi_df = bfi_yrs.merge(
            pop_df.drop(columns="metro_title", errors="ignore"),
            on=["metro13", "year"],
            how="left",
        )
        LOGGER.info("After population merge, rows: %d", len(new_bfi_df))

        LOGGER.info("Merging BFI+population with industry data...")

        # Select available industry columns
        ind_cols = [
            "metro13",
            "year",
            "annual_avg_estabs_count",
            "annual_avg_emplvl",
            "total_annual_wages",
            "annual_avg_wkly_wage",
        ]
        available_ind_cols = [c for c in ind_cols if c in merged_all_ind.columns]

        new_bfi_df = new_bfi_df.merge(
            merged_all_ind[available_ind_cols],
            on=["metro13", "year"],
            how="left",
        )
        LOGGER.info("After industry merge, final rows: %d", len(new_bfi_df))

        # Rename cols if they exist
        rename_map = {
            "race/sex indicator": "race/sex_indicator",
            "total population": "total_population",
        }
        new_bfi_df = new_bfi_df.rename(columns=rename_map)

        # Write to CSV
        if output_path is not None:
            output_path = Path(output_path)
            new_bfi_df.to_csv(output_path, index=False)
            LOGGER.info("Wrote combined BFI dataset to %s", output_path)

        return new_bfi_df

    except Exception:
        LOGGER.error("Unexpected error during final BFI merge.", exc_info=True)
        return None


def main() -> tuple[dict, dict, dict]:
    """Combines all functions to produce merged_bfi.csv and return table dicts."""
    LOGGER.info("--- Starting Main Data Pipeline ---")

    # Download and pre-load necessary datasets
    get_census_pop()
    get_ubls_labor()
    get_uber_county_cbsa_crosswalk()

    # 1. Load and clean BFI
    bfi_df = get_bfi()
    if bfi_df is None:
        return {}, {}, {}

    bfi_df = clean_bfi(bfi_df)
    if bfi_df is None:
        return {}, {}, {}

    # 2. 1980 Pipeline
    LOGGER.info("--- Processing 1980 Data ---")
    raw_pop_1980 = get_pop_1980()
    if raw_pop_1980 is None:
        return {}, {}, {}

    pop_1980 = clean_pop_1980(raw_pop_1980)
    if pop_1980 is None:
        return {}, {}, {}

    raw_msa_county = get_cbsa_county_crosswalk()
    if raw_msa_county is None:
        return {}, {}, {}

    msa_county = clean_cbsa_county_crosswalk(raw_msa_county)
    if msa_county is None:
        return {}, {}, {}

    msa_pop_1980 = merge_pop_1980_with_cbsa(pop_1980, msa_county)
    if msa_pop_1980 is None:
        return {}, {}, {}

    merged_pop_1980 = merge_pop_1980_with_bfi(msa_pop_1980, bfi_df)
    if merged_pop_1980 is None:
        return {}, {}, {}

    pop_1980_agg = aggregate_pop_1980(merged_pop_1980)
    if pop_1980_agg is None:
        return {}, {}, {}

    final_pop_1980 = transform_pop_1980_to_final(pop_1980_agg)
    if final_pop_1980 is None:
        return {}, {}, {}

    final_pop_1980 = rename_pop_1980_columns(final_pop_1980)
    if final_pop_1980 is None:
        return {}, {}, {}

    # 3. 2022 Pipeline
    LOGGER.info("--- Processing 2022 Data ---")
    pop_2022 = get_pop_2022()
    if pop_2022 is None:
        return {}, {}, {}

    pop_2022 = clean_pop_2022(pop_2022)
    if pop_2022 is None:
        return {}, {}, {}

    merged_pop_2022 = merge_pop_2022_with_bfi(pop_2022, bfi_df)
    if merged_pop_2022 is None:
        return {}, {}, {}

    min_df_2022 = organize_pop_2022_minimal(merged_pop_2022)
    if min_df_2022 is None:
        return {}, {}, {}

    # 4. Industry Pipeline
    LOGGER.info("--- Processing Industry Data ---")
    all_ind = combine_industries()
    if all_ind is None:
        return {}, {}, {}

    merged_all_ind = merge_industry_with_msa(all_ind, msa_county, bfi_df)
    if merged_all_ind is None:
        return {}, {}, {}

    # 5. Final Output
    LOGGER.info("--- Building Final Datasets ---")
    output_path = DATA_DIR / "merged_bfi.csv"

    new_bfi_df = build_bfi_pop_labor(
        bfi_df=bfi_df,
        final_pop_1980=final_pop_1980,
        min_df_2022=min_df_2022,
        merged_all_ind=merged_all_ind,
        output_path=output_path,
    )

    if new_bfi_df is None:
        LOGGER.error("Pipeline failed at final step.")
        return {}, {}, {}

    # Generate Tables
    pop_1980_table = make_msa_tables(final_pop_1980)
    pop_2022_table = make_msa_tables(min_df_2022)
    labor_table = build_msa_industry_tables(merged_all_ind)

    LOGGER.info("Pipeline executed successfully.")
    return pop_1980_table, pop_2022_table, labor_table


if __name__ == "__main__":
    # Basic logging config if running this script directly
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
