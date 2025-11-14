"""
===============================================================================
 MSA Healthcare + GDP Data Merger
===============================================================================

This script:
  1. Downloads Real GDP data (2018–2023) for all U.S. MSAs from the BEA API.
  2. Calculates percent change from the preceding year.
  3. Merges the GDP data with the healthcare employment dataset.
  4. Saves both the raw GDP and merged datasets in the /data directory.

USAGE:
------
From the project root (recommended):

    python scripts/prepare_msa_healthcare_gdp.py

OUTPUT FILES:
--------------
  data/msa_gdp_percent_change.csv
  data/merged_healthcare_jobs_with_gdp.csv

DEPENDENCIES:
-------------
  pip install pandas requests

===============================================================================
"""

import os
import requests
import pandas as pd


# ------------------------------------------------------
# Configuration
# ------------------------------------------------------
API_KEY = "73110DFA-D36D-4A7C-99C7-183B704E1596"
BASE_URL = "https://apps.bea.gov/api/data"

# Base folder for all outputs
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEALTHCARE_FILE = os.path.join(DATA_DIR, "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv")
GDP_FILE = os.path.join(DATA_DIR, "msa_gdp_percent_change.csv")
MERGED_FILE = os.path.join(DATA_DIR, "merged_healthcare_jobs_with_gdp.csv")


# ------------------------------------------------------
# Step 1: Download and Compute GDP Percent Change
# ------------------------------------------------------
def download_bea_gdp_percent_change(start_year=2018, end_year=2023, output_file=GDP_FILE):
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

        df = pd.DataFrame(rows)
        df["DataValue"] = pd.to_numeric(df["DataValue"], errors="coerce")

        pivot_df = (
            df.pivot_table(
                index=["GeoFips", "GeoName"],
                columns="TimePeriod",
                values="DataValue",
                aggfunc="first",
            )
            .reset_index()
        )

        # Calculate percent change
        year_cols = sorted([c for c in pivot_df.columns if str(c).isdigit()])
        level_data = pivot_df.copy()
        for i in range(1, len(year_cols)):
            curr, prev = year_cols[i], year_cols[i - 1]
            pivot_df[curr] = ((level_data[curr] - level_data[prev]) / level_data[prev] * 100).round(1)

        pivot_df.drop(columns=[year_cols[0]], inplace=True)
        pivot_df.to_csv(output_file, index=False)
        print(f"✅ GDP data saved at: {os.path.abspath(output_file)}")
        return pivot_df

    except Exception as e:
        print(f"❌ Error downloading GDP data: {e}")
        return None


# ------------------------------------------------------
# Step 2: Merge Healthcare Dataset with GDP
# ------------------------------------------------------
def merge_healthcare_with_gdp(
    healthcare_path=HEALTHCARE_FILE, gdp_path=GDP_FILE, output_path=MERGED_FILE
):
    """Merge BEA GDP percent change data with healthcare employment dataset."""
    print("🔄 Merging healthcare dataset with GDP data...")

    if not os.path.exists(healthcare_path):
        print(f"❌ Healthcare dataset not found: {healthcare_path}")
        return None

    if not os.path.exists(gdp_path):
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

    merged = pd.merge(
        rise,
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

    merged.drop(columns=["GeoFips"], inplace=True)
    merged.to_csv(output_path, index=False)
    print(f"✅ Merged dataset saved at: {os.path.abspath(output_path)}")
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
            print("\n🎉 COMPLETE! Your merged dataset is ready for analysis.")
            print(f"   ➜ Output: {os.path.abspath(MERGED_FILE)}")
        else:
            print("⚠️ Merge step failed.")
    else:
        print("⚠️ GDP data download failed.")
