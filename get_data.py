"""Code to directly get raw data from their sources and save them in /data

Includes one function for each supplementary csv
"""

import io
import logging
import os
import zipfile
from pathlib import Path

import requests
from requests.exceptions import ReadTimeout, RequestException

RAW_DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
RAW_DATA_DIR.mkdir(exist_ok=True)

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

LOGGER = logging.getLogger(__name__)


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
            LOGGER.error("Expected file was NOT found inside the ZIP:\n %s", path)
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
        LOGGER.error("Failed to download 2013 crosswalk data from %s", url)
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

    LOGGER.info("Saved cbsatocountycrosswalk.csv to %s", output_file.resolve())
    return


if __name__ == "__main__":
    get_census_pop()
    get_ubls_labor()
    get_uber_county_cbsa_crosswalk()
