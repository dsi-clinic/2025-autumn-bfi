"""Data preprocessing script (in three parts)

Part 1: GeoJSON Shapefile Preparation

This part of the script:
1. Downloads, extracts, and converts shapefiles to GeoJSON format
2. Prepares combined GeoJSON for US metropolitan areas and states.

url sources: United States Census Bureau
- CBSA shapefile: https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_cbsa_5m.zip
- State shapefile: https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip

OUTPUT FILES:
--------------
  data/combined_US_regions_auto.geojson

Part 2: MSA Healthcare + GDP Data Merger

This part of the script:
  1. Downloads Real GDP data (2018–2023) for all U.S. MSAs from the BEA API.
  2. Calculates percent change from the preceding year.
  3. Merges the GDP data with the healthcare employment dataset.
  4. Saves both the raw GDP and merged datasets in the /data directory.

OUTPUT FILES:
--------------
  data/msa_gdp_percent_change.csv
  data/merged_healthcare_jobs_with_gdp.csv

Part 3: Other Data Prep (Labour, Population, Crosswalks)

This part of the script:
  1. Downloads Real GDP data (2018–2023) for all U.S. MSAs from the BEA API.
  2. Calculates percent change from the preceding year.
  3. Merges the GDP data with the healthcare employment dataset.
  4. Saves both the raw GDP and merged datasets in the /data directory.

OUTPUT FILES:
--------------
  data/merged_bfi.csv

DEPENDENCIES:
-------------
  pip install time zipfile pathlib pandas requests geopandas shutil pathlib rich
"""

import logging
import shutil
import sys
import time
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track

import gt_utilities.census_bea_pipeline as pipeline
import gt_utilities.config as config
import gt_utilities.dataprep_utils as dp_utils

# ------------------------------------------------------
# Configuration & Setup
# ------------------------------------------------------
# 1. Initialize Rich Console for pretty titles/rules
console = Console()

# 2. Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger("preprocessing")

# 3. Path Setup
PROJECT_ROOT: Path = config.PROJECT_ROOT
DATA_DIR: Path = config.DATA_DIR
RAW_DATA_DIR: Path = config.RAW_DATA_DIR
COMBINED_GEOJSON: Path = config.COMBINED_GEOJSON
DATA_PATHS = config.DATA_PATHS
GDP_FILE = config.GDP_FILE
MERGED_FILE = config.GDP_PATHS
MERGED_BFI = config.MERGED_PATHS

if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
if not RAW_DATA_DIR.exists():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_geojson() -> None:
    """Ensure combined_US_regions_auto.geojson exists (Part 1 only).

    Idempotent: does nothing if the file already exists. Used by the Streamlit app
    on first load when deploying without a pre-run Dockerfile (e.g. Streamlit Cloud).
    """
    if COMBINED_GEOJSON.exists():
        return
    logger.info("GeoJSON missing; running Part 1 (GeoJSON shapefile preparation)...")
    extract_path_cbsa = DATA_DIR / "cb_2021_us_cbsa_5m"
    extract_path_state = DATA_DIR / "cb_2021_us_state_5m"

    dp_utils.download_and_extract_shapefile(
        url="https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_cbsa_5m.zip",
        extract_dir=extract_path_cbsa,
    )
    dp_utils.download_and_extract_shapefile(
        url="https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip",
        extract_dir=extract_path_state,
    )
    logger.info("Downloaded and extracted State shapefiles.")

    datadf = pd.read_csv(DATA_PATHS)
    indicator_cols = ["metro13", "metro_title"]
    value_cols = [c for c in datadf.columns if c not in indicator_cols]
    df_long = datadf.melt(
        id_vars=indicator_cols,
        value_vars=value_cols,
        var_name="indicator",
        value_name="value",
    )

    shp_dirs = {"cbsa": extract_path_cbsa, "states": extract_path_state}
    msa_path = DATA_DIR / "2021_US_CBSA_auto.geojson"
    states_path = DATA_DIR / "2021_US_States_auto.geojson"
    out_paths = {"cbsa": msa_path, "states": states_path}
    dp_utils.convert_shapefiles_to_geojson(shp_dirs, out_paths)

    dp_utils.build_combined_geojson(
        df_long=df_long,
        msa_path=msa_path,
        states_path=states_path,
        data_dir=DATA_DIR,
    )

    for folder in [extract_path_cbsa, extract_path_state]:
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder)
    for path in [msa_path, states_path]:
        if path.exists() and path.is_file():
            path.unlink()
    logger.info("Part 1 (GeoJSON) complete: %s", COMBINED_GEOJSON.name)


def ensure_merged_data() -> None:
    """Ensure Part 2 and Part 3 outputs exist (GDP merge + merged BFI).

    Idempotent: skips each part if its outputs already exist. Used by the Streamlit
    app when deploying without a pre-run Dockerfile (e.g. Streamlit Cloud).
    """
    # Part 2: merged_healthcare_jobs_with_gdp.csv (+ msa_gdp_percent_change.csv)
    if not (GDP_FILE.exists() and MERGED_FILE.exists()):
        logger.info("Part 2 outputs missing; running MSA Healthcare + GDP pipeline...")
        gdp_df = dp_utils.download_bea_gdp_percent_change()
        if gdp_df is not None:
            dp_utils.merge_healthcare_with_gdp(DATA_PATHS, GDP_FILE, MERGED_FILE)
            logger.info("Part 2 complete: %s", MERGED_FILE.name)
        else:
            logger.error("Part 2 failed: GDP data download failed.")

    # Part 3: merged_bfi.csv
    if not MERGED_BFI.exists():
        logger.info("Part 3 output missing; running BFI pipeline...")
        pipeline.run_full_pipeline()
        if RAW_DATA_DIR.exists() and RAW_DATA_DIR.is_dir():
            shutil.rmtree(RAW_DATA_DIR)
        logger.info("Part 3 complete: %s", MERGED_BFI.name)


def run_preprocessing() -> None:
    """Runs the full data preprocessing pipeline in three parts."""
    console.rule("[bold blue]Data Preparation Package")
    console.print(
        "Your data preprocessing will commence shortly.\n"
        "After processing, the [bold cyan]'data'[/] folder will be populated by four output files."
        "\n1) 'combined_US_regions_auto.geojson' (combined GeoJSON for MSAs and states for mapping)"
        "\n2) 'merged_healthcare_jobs_with_gdp.csv' (merged healthcare + GDP dataset)"
        "\n3) 'msa_gdp_percent_change.csv' (BEA GDP percent change data)"
        "\n4) 'merged_bfi.csv' (merged dataset for population, GDP etc.)"
    )

    for _ in track(range(40), description="Initializing pipeline..."):
        time.sleep(0.125)

    # ------------------------------------------------------
    # Part 1: GeoJSON Shapefile Preparation
    # ------------------------------------------------------
    console.rule("[bold green]Part 1: GeoJSON Shapefile Preparation")
    if COMBINED_GEOJSON.exists():
        logger.warning(
            f"GeoJSON already present at {COMBINED_GEOJSON.name}. Skipping Part 1."
        )
    else:
        ensure_geojson()
        logger.info("[bold green]Part 1 Complete![/]", extra={"markup": True})

    time.sleep(1)

    # ------------------------------------------------------
    # Part 2: MSA Healthcare + GDP Data Merger
    # ------------------------------------------------------
    console.rule("[bold green]Part 2: MSA Healthcare + GDP Data Merger")

    if GDP_FILE.exists() and MERGED_FILE.exists():
        logger.warning("GDP and Merged datasets already exist. Skipping Part 2.")
    else:
        logger.info("Running MSA Healthcare + GDP Pipeline...")

        gdp_df = dp_utils.download_bea_gdp_percent_change()

        if gdp_df is not None:
            merged_df = dp_utils.merge_healthcare_with_gdp(
                DATA_PATHS, GDP_FILE, MERGED_FILE
            )
            if merged_df is not None:
                logger.info(f"Output saved to: {MERGED_FILE.resolve()}")
                logger.info("[bold green]Part 2 Complete![/]", extra={"markup": True})
            else:
                logger.error("Merge step failed.")
        else:
            logger.error("GDP data download failed.")

    time.sleep(1)

    # ------------------------------------------------------
    # Part 3: Other Data Prep
    # ------------------------------------------------------
    console.rule("[bold green]Part 3: Merged BFI Data Preparation")

    if MERGED_BFI.exists():
        logger.warning("Merged BFI data already present. Skipping Part 3.")
    else:
        logger.info("Running BFI Pipeline...")

        # Runs entire BFI data prep pipeline
        pipeline.run_full_pipeline()

        folder = RAW_DATA_DIR
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder)
            logger.info(f"Deleted folder: {folder.name}")

        logger.info("[bold green]Part 3 Complete![/]", extra={"markup": True})

    # Final Success Message
    console.rule("[bold blue]Pipeline Finished")
    console.print("[bold green]All data preprocessing tasks successfully completed![/]")


if __name__ == "__main__":
    try:
        run_preprocessing()
    except Exception:
        logger.exception("An unhandled exception occurred during preprocessing")
        sys.exit(1)
