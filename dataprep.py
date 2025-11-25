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

import io
import json
import shutil

# import logging
import sys
import time
import zipfile
from pathlib import Path

# from typing import Any
import geopandas as gpd
import pandas as pd
import requests

from gt_utilities import find_project_root

# ------------------------------------------------------
# Part 1: GeoJSON Shapefile Preparation
# ------------------------------------------------------
PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data"

print("\n" + "=" * 80)
print(
    "Welcome to the Data Preparation Package! Your data preprocessing will commence in 5 seconds."
    "\n After processing, check the 'data' folder for the output files. You should see three files:"
    "\n 1) 'combined_US_regions_auto.geojson' (combined GeoJSON for MSAs and states)"
    "\n 2) 'merged_healthcare_jobs_with_gdp.csv' (merged healthcare + GDP dataset)"
    "\n 3) 'msa_gdp_percent_change.csv' (BEA GDP percent change data)"
)

for i in range(40):
    sys.stdout.write("\r{}>".format("==" * i))
    sys.stdout.flush()
    time.sleep(0.125)

print("\n Downloading shapefiles...")

url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_cbsa_5m.zip"

r = requests.get(url, timeout=10)
z = zipfile.ZipFile(io.BytesIO(r.content))
extract_path_cbsa = DATA_DIR / "cb_2021_us_cbsa_5m"
z.extractall(extract_path_cbsa)
z.close()

print("Downloaded and extracted CBSA shapefiles.")
time.sleep(2)

url2 = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip"

r2 = requests.get(url2, timeout=10)
z2 = zipfile.ZipFile(io.BytesIO(r2.content))
extract_path_state = DATA_DIR / "cb_2021_us_state_5m"
z2.extractall(extract_path_state)
z2.close()

print("Downloaded and extracted State shapefiles.")

# Convert extracted shapefiles to GeoJSON

DATA_PATH = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
datadf = pd.read_csv(DATA_PATH)
# Reshape df to long format
value_cols = [c for c in datadf.columns if c not in ["metro13", "metro_title"]]
df_long = datadf.melt(
    id_vars=["metro13", "metro_title"],
    value_vars=value_cols,
    var_name="indicator",
    value_name="value",
)

print("Processing shapefiles to GeoJSON format...")

shp_dirs = {
    "cbsa": extract_path_cbsa,
    "states": extract_path_state,
}

msa_path = DATA_DIR / "2021_US_CBSA_auto.geojson"
states_path = DATA_DIR / "2021_US_States_auto.geojson"

out_paths = {
    "cbsa": msa_path,
    "states": states_path,
}

EPSG_WGS84 = 4326

for key, d in shp_dirs.items():
    shp_files = sorted(d.glob("*.shp"))
    if not shp_files:
        print(f"No .shp found in {d!s}; skipping {key}")
        continue

    shp_path = shp_files[0]
    gdf = gpd.read_file(shp_path)

    # ensure WGS84 (GeoJSON-friendly)

    if gdf.crs is None or gdf.crs.to_epsg() != EPSG_WGS84:
        gdf = gdf.to_crs(epsg=EPSG_WGS84)

    # keep common identifier/name columns where available
    if key == "cbsa":
        id_cols = [c for c in ("CBSAFP", "GEOID", "NAME") if c in gdf.columns]
    else:
        id_cols = [
            c for c in ("STATEFP", "STUSPS", "GEOID", "NAME") if c in gdf.columns
        ]

    # cast identifier columns to string to avoid numeric/float issues in GeoJSON props
    for c in id_cols:
        gdf[c] = gdf[c].astype(str)

    # write GeoJSON
    out = out_paths[key]
    gdf.to_file(out, driver="GeoJSON")
    print(f"Wrote {len(gdf)} features to {out}")

# --- Load the original GeoJSONs
gdf_msas = gpd.read_file(msa_path)
gdf_states = gpd.read_file(states_path)
print("Filtering, Clipping and Processing GeoJSON features...")

# --- Filter MSAs to only those you have data for
msa_ids_with_data = df_long["metro13"].astype(str).unique()
gdf_msas_data = gdf_msas[gdf_msas["CBSAFP"].astype(str).isin(msa_ids_with_data)]

# --- Clip states: remove only the MSAs that have data
gdf_states_clipped = gdf_states.overlay(gdf_msas_data, how="difference")

# --- Save for later use
clipped_states_path = DATA_DIR / "2021_US_States_clipped_auto.geojson"
gdf_states_clipped.to_file(clipped_states_path, driver="GeoJSON")

# --- Load clipped states and filtered MSAs
with msa_path.open(encoding="utf-8") as f:
    msa_geo = json.load(f)
with states_path.open(encoding="utf-8") as f:
    states_geo = json.load(f)

# --- Normalize feature IDs ---
for feat in msa_geo["features"]:
    feat["properties"]["region_id"] = feat["properties"]["CBSAFP"]

for feat in states_geo["features"]:
    feat["properties"]["region_id"] = feat["properties"]["STATEFP"].lstrip("0")

combined_geo = {
    "type": "FeatureCollection",
    "features": msa_geo["features"] + states_geo["features"],
}

output_path = DATA_DIR / "combined_US_regions_auto.geojson"

with output_path.open("w", encoding="utf-8") as f:
    json.dump(combined_geo, f, ensure_ascii=False, indent=2, default=str)
    print(
        f"Wrote {len(gdf_states_clipped) + len(gdf_msas_data)} features to {output_path}"
    )

# Cleanup intermediate files
print("Cleaning up intermediate files...")

# FOLDERS TO DELETE
folders_to_delete = [extract_path_cbsa, extract_path_state]

# FILES TO DELETE
files_to_delete = [clipped_states_path, msa_path, states_path]

# Delete folders
for folder in folders_to_delete:
    if folder.exists() and folder.is_dir():
        shutil.rmtree(folder)
        print(f"Deleted folder: {folder}")

# Delete files
for file in files_to_delete:
    if file.exists() and file.is_file():
        file.unlink()
        print(f"Deleted file: {file}")

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

# Base folder for all outputs
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEALTHCARE_FILE = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
GDP_FILE = DATA_DIR / "msa_gdp_percent_change.csv"
MERGED_FILE = DATA_DIR / "merged_healthcare_jobs_with_gdp.csv"


# ------------------------------------------------------
# Step 1: Download and Compute GDP Percent Change
# ------------------------------------------------------
def download_bea_gdp_percent_change(
    start_year: int = 2018, end_year: int = 2023, output_file: Path = GDP_FILE
) -> pd.DataFrame | None:
    """Download BEA GDP data for all MSAs and calculate percent change."""
    years = ",".join(str(y) for y in range(start_year, end_year + 1))
    params = {
        "UserID": API_KEY,
        "method": "GetData",
        "datasetname": "Regional",
        "TableName": "CAGDP1",
        "LineCode": "1",  # Real GDP (thousands of chained 2017 dollars)
        "Year": years,
        "GeoFips": "MSA",
        "ResultFormat": "json",
    }

    try:
        print(f"📡 Downloading BEA GDP data ({start_year}-{end_year})...")
        response = requests.get(BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "BEAAPI" not in data or "Results" not in data["BEAAPI"]:
            print("⚠️ Unexpected API response format.")
            return None

        rows = data["BEAAPI"]["Results"].get("Data", [])
        if not rows:
            print("⚠️ No data returned from BEA API.")
            return None

        rows_df = pd.DataFrame(rows)
        rows_df["DataValue"] = pd.to_numeric(rows_df["DataValue"], errors="coerce")

        pivot_df = rows_df.pivot_table(
            index=["GeoFips", "GeoName"],
            columns="TimePeriod",
            values="DataValue",
            aggfunc="first",
        ).reset_index()

        # Calculate percent change
        year_cols = sorted([c for c in pivot_df.columns if str(c).isdigit()])
        level_data = pivot_df.copy()
        for i in range(1, len(year_cols)):
            curr, prev = year_cols[i], year_cols[i - 1]
            pivot_df[curr] = (
                (level_data[curr] - level_data[prev]) / level_data[prev] * 100
            ).round(1)

        pivot_df = pivot_df.drop(columns=[year_cols[0]])
        pivot_df.to_csv(output_file, index=False)
        print(f"✅ GDP data saved at: {output_file.resolve()}")
        return pivot_df

    except Exception as e:
        print(f"❌ Error downloading GDP data: {e}")
        return None


# ------------------------------------------------------
# Step 2: Merge Healthcare Dataset with GDP
# ------------------------------------------------------
def merge_healthcare_with_gdp(
    healthcare_path: Path = HEALTHCARE_FILE,
    gdp_path: Path = GDP_FILE,
    output_path: Path = MERGED_FILE,
) -> pd.DataFrame | None:
    """Merge BEA GDP percent change data with healthcare employment dataset."""
    print("🔄 Merging healthcare dataset with GDP data...")

    if not healthcare_path.exists():
        print(f"❌ Healthcare dataset not found: {healthcare_path}")
        return None

    if not gdp_path.exists():
        print(f"❌ GDP dataset not found: {gdp_path}")
        return None

    rise = pd.read_csv(healthcare_path)
    gdp = pd.read_csv(gdp_path)

    rise["metro13"] = pd.to_numeric(rise["metro13"], errors="coerce")
    gdp["GeoFips"] = pd.to_numeric(gdp["GeoFips"], errors="coerce")

    # Keep only matching MSAs
    rise = rise[rise["metro13"].isin(gdp["GeoFips"])].copy()

    # Rename GDP columns
    gdp = gdp.rename(
        columns={
            "2019": "gdp_growth_2019_percent",
            "2020": "gdp_growth_2020_percent",
            "2021": "gdp_growth_2021_percent",
            "2022": "gdp_growth_2022_percent",
            "2023": "gdp_growth_2023_percent",
        }
    )

    merged = rise.merge(
        gdp[
            [
                "GeoFips",
                "gdp_growth_2019_percent",
                "gdp_growth_2020_percent",
                "gdp_growth_2021_percent",
                "gdp_growth_2022_percent",
                "gdp_growth_2023_percent",
            ]
        ],
        left_on="metro13",
        right_on="GeoFips",
        how="left",
    )

    merged = merged.drop(columns=["GeoFips"])
    merged.to_csv(output_path, index=False)
    print(f"✅ Merged dataset saved at: {output_path.resolve()}")
    print(f"   Rows: {len(merged):,} | Columns: {len(merged.columns)}")
    return merged


# ------------------------------------------------------
# Step 3: Run Entire Pipeline
# ------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🏙️  Running MSA Healthcare + GDP Data Preparation Pipeline")
    print("=" * 80)

    gdp_df = download_bea_gdp_percent_change()
    if gdp_df is not None:
        merged_df = merge_healthcare_with_gdp()
        if merged_df is not None:
            print("\n🎉 COMPLETE! Your datasets are ready. (2/2)")
            print(f"   ➜ Output: {MERGED_FILE.resolve()}")
        else:
            print("⚠️ Merge step failed.")
    else:
        print("⚠️ GDP data download failed.")
