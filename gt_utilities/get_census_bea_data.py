"""Supplementary analysis using 1980 and 2022 population and labor data.

This file first obtains raw data and saves them in /data/raw_data.
"""

import io
import logging
import zipfile

import pandas as pd
import requests
from requests.exceptions import ReadTimeout, RequestException

from gt_utilities import setup_logger
from gt_utilities.config import (
    DATA_DIR,
    NBER_COUNTY_CBSA_CROSSWALK_URL,
    RAW_CENSUS_POP_DATA_URLS,
    RAW_DATA_DIR,
    UBLA_LABOR_DATA_ZIP_URLS_AND_RAW_PATHS,
)

LOGGER: logging.Logger = setup_logger(__name__)


def get_census_pop(data_urls: dict[str, str] = RAW_CENSUS_POP_DATA_URLS) -> None:
    """Gets csvs containing 1980 and 2022 population data.

    From US Census Bureau at:
    https://www2.census.gov/programs-surveys/popest/
    """
    for url, year in data_urls.items():
        try:
            LOGGER.info("Requesting %s Census data...", year)
            r: requests.Response = requests.get(url, timeout=30)
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
        year: str = "1980" if "1980" in zip_url else "2022"

        try:
            LOGGER.info("Requesting %s Labor data (ZIP)...", year)
            r: requests.Response = requests.get(zip_url, timeout=30)
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
        r: requests.Response = requests.get(url, timeout=30)
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
        pop: pd.DataFrame = pd.read_csv(csv_path, skiprows=5, header=0)
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
        bfi_df: pd.DataFrame = pd.read_csv(csv_path)
        LOGGER.info("Loaded BFI csv. Shape: %s", bfi_df.shape)
        return bfi_df
    except Exception as exc:
        LOGGER.error("Error reading BFI csv: %s", exc, exc_info=True)
        return None


def get_cbsa_county_crosswalk() -> pd.DataFrame | None:
    """Retrieves the cbsa to county crosswalk csv."""
    csv_path = RAW_DATA_DIR / "cbsatocountycrosswalk.csv"
    LOGGER.info("Loading crosswalk from %s", csv_path)

    try:
        msa_county: pd.DataFrame = pd.read_csv(csv_path, encoding="latin1")
        LOGGER.info("Loaded crosswalk. Shape: %s", msa_county.shape)
        return msa_county
    except Exception as exc:
        LOGGER.error("Error reading crosswalk: %s", exc, exc_info=True)
        return None


def get_pop_2022() -> pd.DataFrame | None:
    """Returns cleaned 2022 population dataframe.

    Loads the 2022 population CSV from raw_data, filters to the correct year,
    drops unused columns, and returns a cleaned dataframe.
    """
    file_path = RAW_DATA_DIR / "pop_2022.csv"
    LOGGER.info("Beginning load of 2022 population data from %s", file_path)

    # load file
    try:
        pop2: pd.DataFrame = pd.read_csv(file_path, encoding="latin1")
        LOGGER.info("Successfully loaded pop_2022.csv with %d rows.", pop2.shape[0])
    except FileNotFoundError:
        LOGGER.error("pop_2022.csv not found at path: %s", file_path)
        return None
    except Exception as exc:
        LOGGER.error("Failed to read pop_2022.csv: %s", exc, exc_info=True)
        return None

    # drop irrelevant columns
    drop_cols: list[str] = ["MDIV", "LSAD", "SUMLEV"]
    missing: list[str] = [c for c in drop_cols if c not in pop2.columns]
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
        before: int = pop2.shape[0]
        # Querying for YEAR == 4 (2022 estimate)
        if "YEAR" in pop2.columns:
            pop2 = pop2.query("`YEAR` == 4").copy()
            after: int = pop2.shape[0]
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
        ind_df: pd.DataFrame = pd.read_csv(file_path)
        LOGGER.info("Successfully read labor_%s.csv with shape %s", year, ind_df.shape)
    except FileNotFoundError:
        LOGGER.error("labor_%s.csv not found at %s", year, file_path)
        return None
    except Exception as exc:
        LOGGER.error("Failed to read labor_%s.csv: %s", year, exc, exc_info=True)
        return None

    # drop unnecessary columns
    drop_cols: list[str] = ["own_code", "industry_code", "qtr", "disclosure_code"]
    existing_drop_cols: list[str] = [c for c in drop_cols if c in ind_df.columns]

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
        area_numeric: pd.Series = pd.to_numeric(ind_df["area_fips"], errors="coerce")

        bad_codes: pd.Series = ind_df.loc[area_numeric.isna(), "area_fips"].unique()
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


if __name__ == "__main__":
    # Setup basic logging to see output
    logging.basicConfig(level=logging.INFO)

    print("Running GETTER in isolation...")

    get_census_pop()
    get_ubls_labor()
    get_uber_county_cbsa_crosswalk()
    print("Downloads complete.")
