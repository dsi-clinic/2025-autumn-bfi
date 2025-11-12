"""Code to directly get raw data from their sources and save them in /data

Includes one function for each supplementary csv
"""

import io
import zipfile
from pathlib import Path

import requests

SAVE_PATH = Path("data/")


def get_1980_pop() -> None:
    """Gets csv containing 1980 population data.

    From US Census Bureau.
    """
    url = "https://www2.census.gov/programs-surveys/popest/datasets/1980-1990/counties/asrh/pe-02.csv"

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    output_file = SAVE_PATH / "pop_1980.csv"

    with output_file.open("wb") as f:
        f.write(r.content)

    print("Saved pop_1980.csv to", output_file.resolve())
    return


def get_2022_pop() -> None:
    """Gets csv containing 2022 population data.

    From US Census Bureau.
    """
    url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/metro/asrh/cbsa-est2023-alldata-char.csv"

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    output_file = SAVE_PATH / "pop_2022.csv"

    with output_file.open("wb") as f:
        f.write(r.content)

    print("Saved pop_2022.csv to", output_file.resolve())
    return


def get_1980_labor() -> None:
    """Unzips folder containing 1980 employment data for all industries.

    From US Bureau of Labor Statistics.
    """
    url = "https://data.bls.gov/cew/data/files/1980/sic/csv/sic_1980_annual_by_industry.zip"

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    output_file = SAVE_PATH / "labor_1980.csv"

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        with (
            z.open(
                "sic.1980.annual.by_industry/sic.1980.annual 0Z (All Industries).csv"
            ) as source,
            output_file.open("wb") as target,
        ):
            target.write(source.read())

    print("Saved labor_1980.csv to", output_file.resolve())
    return


def get_2022_labor() -> None:
    """Unzips folder containing 2022 employment data for all industries.

    From US Bureau of Labor Statistics.
    """
    url = "https://data.bls.gov/cew/data/files/2022/csv/2022_annual_by_industry.zip"

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    output_file = SAVE_PATH / "labor_2022.csv"

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        with (
            z.open(
                "2022.annual.by_industry/2022.annual 10 10 Total, all industries.csv"
            ) as source,
            output_file.open("wb") as target,
        ):
            target.write(source.read())

    print("Saved labor_2022.csv to", output_file.resolve())
    return


if __name__ == "__main__":
    get_1980_pop()
    get_2022_pop()
    get_1980_labor()
    get_2022_labor()
