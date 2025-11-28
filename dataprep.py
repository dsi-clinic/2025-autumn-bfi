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
  data/msa_gdp_percent_change.csv
  data/merged_healthcare_jobs_with_gdp.csv

DEPENDENCIES:
-------------
  pip install time io json zipfile pathlib pandas requests geopandas shutil pathlib
"""

import logging
import shutil
import sys
import time

# from pathlib import Path
import pandas as pd

import gt_utilities.dataprep_utils as dp_utils

# import requests
from gt_utilities import find_project_root

# ------------------------------------------------------
# Configuration
# ------------------------------------------------------

PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data"

COMBINED_GEOJSON = DATA_DIR / "combined_US_regions_auto.geojson"

DATA_PATHS = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"

GDP_FILE = DATA_DIR / "msa_gdp_percent_change.csv"
MERGED_FILE = DATA_DIR / "merged_healthcare_jobs_with_gdp.csv"

# ------------------------------------------------------
# Part 1: GeoJSON Shapefile Preparation
# ------------------------------------------------------

if DATA_DIR.exists() is False:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

print("\n" + "=" * 80)
print(
    "Welcome to the Data Preparation Package! Your data preprocessing will commence in 5 seconds."
    "\nAfter processing, the 'data' folder will be populated by three output files:"
    "\n1) 'combined_US_regions_auto.geojson' (combined GeoJSON for MSAs and states for mapping)"
    "\n2) 'merged_healthcare_jobs_with_gdp.csv' (merged healthcare + GDP dataset)"
    "\n3) 'msa_gdp_percent_change.csv' (BEA GDP percent change data)"
)

for i in range(40):
    sys.stdout.write("\r{}>".format("==" * i))
    sys.stdout.flush()
    time.sleep(0.125)

if COMBINED_GEOJSON.exists():
    print("\nGeoJSON already present. Skipping to Part 2... (1/2)")
else:
    print("\nDownloading shapefiles...")

    extract_path_cbsa = DATA_DIR / "cb_2021_us_cbsa_5m"
    extract_path_state = DATA_DIR / "cb_2021_us_state_5m"

    dp_utils.download_and_extract_shapefile(
        url="https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_cbsa_5m.zip",
        extract_dir=extract_path_cbsa,
    )

    time.sleep(2)

    dp_utils.download_and_extract_shapefile(
        url="https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip",
        extract_dir=extract_path_state,
    )

    print("Downloaded and extracted State shapefiles.")

    # Data preprocessing: Loading BFI healthcare dataset and reshaping to long format

    DATA_PATH = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
    datadf = pd.read_csv(DATA_PATH)
    indicator_cols = ["metro13", "metro_title"]
    value_cols = [c for c in datadf.columns if c not in indicator_cols]
    df_long = datadf.melt(
        id_vars=indicator_cols,
        value_vars=value_cols,
        var_name="indicator",
        value_name="value",
    )

    # Convert extracted shapefiles to GeoJSON

    print("Processing shapefiles to GeoJSON format...")

    # Packaging shapefile directories into dictionary for processing
    shp_dirs = {
        "cbsa": extract_path_cbsa,
        "states": extract_path_state,
    }

    msa_path = DATA_DIR / "2021_US_CBSA_auto.geojson"
    states_path = DATA_DIR / "2021_US_States_auto.geojson"

    # Defining output paths for GeoJSON files
    out_paths = {
        "cbsa": msa_path,
        "states": states_path,
    }

    dp_utils.convert_shapefiles_to_geojson(shp_dirs, out_paths)

    # Filtering, Clipping, and Processing GeoJSON features

    dp_utils.build_combined_geojson(
        msa_path=msa_path, states_path=states_path, df_long=df_long, data_dir=DATA_DIR
    )

    # Cleanup intermediate files
    logger.info("Cleaning up intermediate files...")

    # FOLDERS TO DELETE
    folders_to_delete = [extract_path_cbsa, extract_path_state]

    # FILES TO DELETE
    files_to_delete = [msa_path, states_path]

    # Delete folders
    for folder in folders_to_delete:
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder)
            logger.info(f"Deleted folder: {folder}")

    # Delete files
    for file in files_to_delete:
        if file.exists() and file.is_file():
            file.unlink()
            logger.info(f"Deleted file: {file}")

    print("\n" + "=" * 80)
    print("Cleanup complete. Shapefile preprocessing complete! (1/2)")
    print("=" * 80)

time.sleep(2)

# ------------------------------------------------------
# Part 2: MSA Healthcare + GDP Data Merger
# ------------------------------------------------------
# Configuration
# ------------------------------------------------------
API_KEY = "73110DFA-D36D-4A7C-99C7-183B704E1596"
BASE_URL = "https://apps.bea.gov/api/data"

# ------------------------------------------------------
# Run Entire Pipeline
# ------------------------------------------------------

if GDP_FILE.exists() and MERGED_FILE.exists():
    print(
        "GDP and Merged datasets already exist. Skipping download and merge steps..."
        "\nAll data preprocessing complete! (2/2)"
    )
else:
    if __name__ == "__main__":
        print("\n" + "=" * 80)
        print("🏙️  Running MSA Healthcare + GDP Data Preparation Pipeline")
        print("=" * 80)

        gdp_df = dp_utils.download_bea_gdp_percent_change()
        if gdp_df is not None:
            merged_df = dp_utils.merge_healthcare_with_gdp(
                DATA_PATHS, GDP_FILE, MERGED_FILE
            )
            if merged_df is not None:
                print("\n" + "=" * 80)
                print("All data preprocessing complete! (2/2)")
                print("=" * 80)
                print(f"   ➜ Output: {MERGED_FILE.resolve()}")
            else:
                print("⚠️ Merge step failed.")
        else:
            print("⚠️ GDP data download failed.")
