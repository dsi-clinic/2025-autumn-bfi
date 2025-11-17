"""
Data processing script for MSA population analysis (1980 and 2022).

This script processes census data from 1980 and 2022, merging it with MSA
information and organizing it for demographic analysis.
"""

import os
from typing import List
import pandas as pd


# -------------------------
# Constants
# -------------------------
DATA_DIR = os.path.expanduser("../data/")

# Input file paths
BFI_FILE = os.path.join(DATA_DIR, "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv")
MSA_COUNTY_FILE = os.path.join(DATA_DIR, "cbsatocountycrosswalk.csv")
POP_1980_FILE = os.path.join(DATA_DIR, "pe-02.csv")
POP_2022_FILE = os.path.join(DATA_DIR, "cbsa-est2023-alldata-char.csv")

# Output file paths
OUTPUT_1980 = os.path.join(DATA_DIR, "merged_pop_1980.csv")
OUTPUT_2022 = os.path.join(DATA_DIR, "min_df_2022.csv")

# Column groups for aggregation
OTHER_MALE_COLS = ["IAC_MALE", "AAC_MALE", "NAC_MALE"]
OTHER_FEMALE_COLS = ["IAC_FEMALE", "AAC_FEMALE", "NAC_FEMALE"]

# Columns to keep in final 2022 dataset
COLS_2022_FINAL = [
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


# -------------------------
# Helper Functions
# -------------------------
def load_bfi_data(filepath: str) -> pd.DataFrame:
    """Load BFI MSA dataset."""
    return pd.read_csv(filepath)


def load_msa_county_crosswalk(filepath: str) -> pd.DataFrame:
    """Load MSA to county crosswalk data."""
    return pd.read_csv(filepath, encoding="latin1")


def load_1980_population(filepath: str) -> pd.DataFrame:
    """
    Load and clean 1980 population data.
    
    Parameters
    ----------
    filepath : str
        Path to the 1980 population CSV file.
    
    Returns
    -------
    pd.DataFrame
        Cleaned 1980 population data.
    """
    # Skip informational header rows
    pop = pd.read_csv(filepath, skiprows=5, header=0)
    # Drop first empty row
    pop = pop.drop(0)
    return pop


def add_total_population(df: pd.DataFrame, start_col_index: int = 3) -> pd.DataFrame:
    """
    Add total population column by summing demographic columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with demographic columns.
    start_col_index : int, default=3
        Index where demographic columns begin.
    
    Returns
    -------
    pd.DataFrame
        Dataframe with added 'Total Population' column.
    """
    cols_to_sum = list(df.columns)[start_col_index:]
    df["Total Population"] = df[cols_to_sum].sum(axis=1)
    return df


def process_1980_data(
    bfi_df: pd.DataFrame,
    msa_county: pd.DataFrame,
    pop_1980_raw: pd.DataFrame
) -> pd.DataFrame:
    """
    Process 1980 population data with MSA information.
    
    Parameters
    ----------
    bfi_df : pd.DataFrame
        BFI MSA reference dataset.
    msa_county : pd.DataFrame
        MSA to county crosswalk.
    pop_1980_raw : pd.DataFrame
        Raw 1980 population data.
    
    Returns
    -------
    pd.DataFrame
        Merged and cleaned 1980 population data with MSA codes.
    """
    # Filter to 1980 data only
    pop_1980 = pop_1980_raw.query("`Year of Estimate` == 1980").copy()
    
    # Add total population column
    pop_1980 = add_total_population(pop_1980)
    
    # Merge with MSA-county crosswalk
    msa_pop_1980 = pop_1980.merge(
        msa_county[["ssacounty", "fipscounty", "cbsaname"]],
        left_on="FIPS State and County Codes",
        right_on="fipscounty",
        how="inner",
    ).drop(columns=["fipscounty"])
    
    # Keep only rows relevant to BFI dataset
    merged_pop_1980 = msa_pop_1980.merge(
        bfi_df[["metro13", "metro_title"]],
        left_on="ssacounty",
        right_on="metro13",
        how="inner",
    ).drop(columns=["ssacounty", "cbsaname"])
    
    return merged_pop_1980


def process_2022_data(bfi_df: pd.DataFrame, pop_2022_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Process 2022 population data with MSA information.
    
    Parameters
    ----------
    bfi_df : pd.DataFrame
        BFI MSA reference dataset.
    pop_2022_raw : pd.DataFrame
        Raw 2022 population data.
    
    Returns
    -------
    pd.DataFrame
        Cleaned 2022 population data organized by race and sex.
    """
    # Drop unnecessary columns
    cols_to_drop = ["MDIV", "LSAD", "SUMLEV"]
    pop2 = pop_2022_raw.drop(columns=cols_to_drop)
    
    # Filter to 2022 estimates (YEAR == 4)
    # 1 = 4/1/2020, 2 = 7/1/2020, 3 = 7/1/2021, 4 = 7/1/2022, 5 = 7/1/2023
    pop2 = pop2.query("`YEAR` == 4").drop(columns=["YEAR"])
    
    # Keep only rows relevant to BFI dataset
    merged_pop_2022 = pop2.merge(
        bfi_df[["metro13", "metro_title"]],
        left_on="CBSA",
        right_on="metro13",
        how="inner",
    ).drop(columns=["CBSA", "NAME"])
    
    # Select and organize columns
    min_df_2022 = merged_pop_2022[COLS_2022_FINAL].copy()
    
    # Aggregate "Other" races (Indian/Alaska Native, Asian, Native Hawaiian)
    min_df_2022["OTHER_MALE"] = merged_pop_2022[OTHER_MALE_COLS].sum(axis=1)
    min_df_2022["OTHER_FEMALE"] = merged_pop_2022[OTHER_FEMALE_COLS].sum(axis=1)
    
    return min_df_2022


# -------------------------
# Main Execution
# -------------------------
def main():
    """Main execution function for processing 1980 and 2022 population data."""
    print("Starting data processing...")
    
    # Load base datasets
    print("Loading base datasets...")
    bfi_df = load_bfi_data(BFI_FILE)
    msa_county = load_msa_county_crosswalk(MSA_COUNTY_FILE)
    
    # Process 1980 data
    print("Processing 1980 population data...")
    pop_1980_raw = load_1980_population(POP_1980_FILE)
    merged_pop_1980 = process_1980_data(bfi_df, msa_county, pop_1980_raw)
    merged_pop_1980.to_csv(OUTPUT_1980, index=False)
    print(f"1980 data saved to {OUTPUT_1980}")
    
    # Process 2022 data
    print("Processing 2022 population data...")
    pop_2022_raw = pd.read_csv(POP_2022_FILE, encoding="latin1")
    min_df_2022 = process_2022_data(bfi_df, pop_2022_raw)
    min_df_2022.to_csv(OUTPUT_2022, index=False)
    print(f"2022 data saved to {OUTPUT_2022}")
    
    print("Data processing complete!")


if __name__ == "__main__":
    main()
