"""Runs entire census bea data pipeline to produce final datasets.

This file combines the four separate modules:
- get_census_bea_data.py
- clean_census_bea_data.py
- merge_census_bea_data.py
- build_census_bea_resources.py
to produce the final merged_bfi.csv and MSA tables.
"""

import logging

import gt_utilities.build_census_bea_resources as builder
import gt_utilities.clean_census_bea_data as cleaner
import gt_utilities.get_census_bea_data as getter
import gt_utilities.merge_census_bea_data as merger
from gt_utilities.config import DATA_DIR

LOGGER = logging.getLogger(__name__)


def run_full_pipeline() -> tuple[dict, dict, dict]:
    """Combines all functions to produce merged_bfi.csv and return table dicts."""
    LOGGER.info("--- Starting Main Data Pipeline ---")

    # Download and pre-load necessary datasets
    getter.get_census_pop()
    getter.get_ubls_labor()
    getter.get_uber_county_cbsa_crosswalk()

    # 1. Load and clean BFI
    bfi_df = getter.get_bfi()
    if bfi_df is None:
        return {}, {}, {}

    bfi_df = cleaner.clean_bfi(bfi_df)
    if bfi_df is None:
        return {}, {}, {}

    # 2. 1980 Pipeline
    LOGGER.info("--- Processing 1980 Data ---")
    raw_pop_1980 = getter.get_pop_1980()
    if raw_pop_1980 is None:
        return {}, {}, {}

    pop_1980 = cleaner.clean_pop_1980(raw_pop_1980)
    if pop_1980 is None:
        return {}, {}, {}

    raw_msa_county = getter.get_cbsa_county_crosswalk()
    if raw_msa_county is None:
        return {}, {}, {}

    msa_county = cleaner.clean_cbsa_county_crosswalk(raw_msa_county)
    if msa_county is None:
        return {}, {}, {}

    msa_pop_1980 = merger.merge_pop_1980_with_cbsa(pop_1980, msa_county)
    if msa_pop_1980 is None:
        return {}, {}, {}

    merged_pop_1980 = merger.merge_pop_1980_with_bfi(msa_pop_1980, bfi_df)
    if merged_pop_1980 is None:
        return {}, {}, {}

    pop_1980_agg = cleaner.aggregate_pop_1980(merged_pop_1980)
    if pop_1980_agg is None:
        return {}, {}, {}

    final_pop_1980 = cleaner.transform_pop_1980_to_final(pop_1980_agg)
    if final_pop_1980 is None:
        return {}, {}, {}

    final_pop_1980 = cleaner.rename_pop_1980_columns(final_pop_1980)
    if final_pop_1980 is None:
        return {}, {}, {}

    # 3. 2022 Pipeline
    LOGGER.info("--- Processing 2022 Data ---")
    pop_2022 = getter.get_pop_2022()
    if pop_2022 is None:
        return {}, {}, {}

    pop_2022 = cleaner.clean_pop_2022(pop_2022)
    if pop_2022 is None:
        return {}, {}, {}

    merged_pop_2022 = merger.merge_pop_2022_with_bfi(pop_2022, bfi_df)
    if merged_pop_2022 is None:
        return {}, {}, {}

    min_df_2022 = cleaner.organize_pop_2022_minimal(merged_pop_2022)
    if min_df_2022 is None:
        return {}, {}, {}

    # 4. Industry Pipeline
    LOGGER.info("--- Processing Industry Data ---")
    all_ind = merger.combine_industries()
    if all_ind is None:
        return {}, {}, {}

    merged_all_ind = merger.merge_industry_with_msa(all_ind, msa_county, bfi_df)
    if merged_all_ind is None:
        return {}, {}, {}

    # 5. Final Output
    LOGGER.info("--- Building Final Datasets ---")
    output_path = DATA_DIR / "merged_bfi.csv"

    new_bfi_df = builder.build_bfi_pop_labor(
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
    pop_1980_table = builder.make_msa_tables(final_pop_1980)
    pop_2022_table = builder.make_msa_tables(min_df_2022)
    labor_table = builder.build_msa_industry_tables(merged_all_ind)

    LOGGER.info("Pipeline executed successfully.")
    return pop_1980_table, pop_2022_table, labor_table


if __name__ == "__main__":
    # Basic logging config if running this script directly
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    run_full_pipeline()
