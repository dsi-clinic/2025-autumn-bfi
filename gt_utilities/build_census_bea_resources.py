"""Builder of census and labor data tables.

This file builds:
- A MSA-level race/sex proportion table given a dataframe
- Summary table for aggregate industry data by MSA and year
"""

import logging
import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "data")).resolve()
RAW_DATA_DIR = DATA_DIR / "raw_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Logger
LOGGER = logging.getLogger(__name__)


def make_msa_tables(final_pop_df: pd.DataFrame) -> dict:  # put this into make_resources
    """Builds MSA-level race/sex proportion tables and logs all steps.

    Parameters:
        final_pop_df (pd.DataFrame): Cleaned 1980 population dataset with MSA codes.

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
