"""Helper functions for ZIP-based shapefile processing."""

import io
import json
import logging
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests

from gt_utilities import setup_logger
from gt_utilities.config import API_KEY, BASE_URL, GDP_FILE

LOGGER: logging.Logger = setup_logger(__name__)


def download_and_extract_shapefile(
    url: str,
    extract_dir: Path,
    timeout: int = 30,
) -> Path:
    """Download a ZIP file containing shapefiles and extract it to a directory.

    Args:
        url: Full HTTPS URL pointing to a ZIP file.
        extract_dir: Directory into which the ZIP contents will be extracted.
        timeout: Request timeout in seconds.

    Returns:
        Path object of the extraction directory.

    Raises:
        requests.RequestException: If download fails.
        zipfile.BadZipFile: If the file is not a valid ZIP archive.
        OSError: If writing files fails.
    """
    extract_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Downloading and extracting shapefiles from: %s", url)

    # --- Download the ZIP ---
    try:
        response: requests.Response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        LOGGER.error("Failed to download file from %s: %s", url, exc, exc_info=True)
        raise exc

    # --- Extract ---
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(extract_dir)
            z.close()
    except zipfile.BadZipFile as exc:
        LOGGER.error("Invalid ZIP file from %s", url)
        raise exc

    LOGGER.info("Extracted shapefiles to: %s", extract_dir.resolve())

    return extract_dir


def convert_shapefiles_to_geojson(
    shp_dirs: dict[str, Path],
    out_paths: dict[str, Path],
    epsg: int = 4326,
) -> None:
    """Convert extracted shapefiles (CBSA, states) to GeoJSON.

    Parameters
    ----------
    shp_dirs : dict[str, Path]
        e.g. {"cbsa": Path(...), "states": Path(...)}
        Each path must contain *.shp extracted already.

    out_paths : dict[str, Path]
        Output GeoJSON paths mapped to same keys ("cbsa", "states").

    epsg : int
        EPSG code for coordinate system (default = 4326/WGS84).
    """
    for key, d in shp_dirs.items():
        if not d.exists():
            LOGGER.warning(f"Shapefile directory does not exist: {d!s}; skipping {key}")
            continue

        shp_files: list[Path] = sorted(d.glob("*.shp"))
        if not shp_files:
            LOGGER.warning(f"No .shp found in {d!s}; skipping {key}")
            continue

        shp_path: Path = shp_files[0]
        try:
            gdf: gpd.GeoDataFrame = gpd.read_file(shp_path)
        except Exception as exc:
            LOGGER.error(f"Failed to read shapefile {shp_path!s}: {exc}", exc_info=True)
            continue

        if gdf.crs is None or gdf.crs.to_epsg() != epsg:
            gdf = gdf.to_crs(epsg=epsg)

        # keep common identifier/name columns (Hardcoded from US Census Bureau naming conventions)
        id_cols: list[str]

        if key == "cbsa":
            id_cols = [c for c in ("CBSAFP", "GEOID", "NAME") if c in gdf.columns]
        else:
            id_cols = [
                c for c in ("STATEFP", "STUSPS", "GEOID", "NAME") if c in gdf.columns
            ]

        # cast identifier columns to string
        for c in id_cols:
            gdf[c] = gdf[c].astype(str)

        # write GeoJSON
        out: Path = out_paths[key]
        try:
            gdf.to_file(out, driver="GeoJSON")
            LOGGER.info(f"Wrote {len(gdf)} features to {out}")
        except Exception as exc:
            LOGGER.error(f"Failed to write GeoJSON to {out!s}: {exc}", exc_info=True)
            continue


def build_combined_geojson(
    df_long: pd.DataFrame,
    msa_path: Path,
    states_path: Path,
    data_dir: Path,
    clipped_states_filename: str = "2021_US_States_clipped_auto.geojson",
    combined_filename: str = "combined_US_regions_auto.geojson",
    clipped_states_keep: bool = False,
) -> None:
    """Build combined GeoJSON consisting of:

    - filtered MSA polygons (only those present in df_long)
    - clipped state polygons (MSAs removed)
    - saved as combined GeoJSON with normalized region IDs.

    Parameters
    ----------
    df_long : pd.DataFrame
        Long-format data including a 'metro13' column.
    msa_path : Path
        Path to the CBSA GeoJSON.
    states_path : Path
        Path to the original States GeoJSON.
    data_dir : Path
        Base directory for saving output files.
    clipped_states_filename : str
        Filename for the clipped states GeoJSON. Default is "2021_US_States_clipped_auto.geojson".
    combined_filename : str
        Output filename for combined regions.
    clipped_states_keep : bool
        Whether to keep the temporary clipped states file. Default is False.
    """
    # --- Load original GeoJSONs ---
    LOGGER.info("Filtering, Clipping, and Processing GeoJSON features...")
    try:
        gdf_msas: gpd.GeoDataFrame = gpd.read_file(msa_path)
        gdf_states: gpd.GeoDataFrame = gpd.read_file(states_path)
    except Exception as exc:
        LOGGER.error("Error reading input GeoJSONs: %s", exc, exc_info=True)
        raise exc

    # Filtering MSAs to those present in df_long (Hardcoded according to original Census Bureau files)
    msa_ids: Any = df_long["metro13"].astype(str).unique()
    gdf_msas_filtered: gpd.GeoDataFrame = gdf_msas[
        gdf_msas["CBSAFP"].astype(str).isin(msa_ids)
    ]
    LOGGER.info(f"Filtered to {len(gdf_msas_filtered)} MSAs with available data.")

    # --- Clip states by removing MSAs ---
    gdf_states_clipped: gpd.GeoDataFrame = gdf_states.overlay(
        gdf_msas_filtered, how="difference"
    )
    LOGGER.info(f"Clipped states: {len(gdf_states_clipped)} features remain.")

    # --- Save clipped states ---
    clipped_states_path: Path = data_dir / clipped_states_filename
    gdf_states_clipped.to_file(clipped_states_path, driver="GeoJSON")
    LOGGER.info(f"Wrote clipped states GeoJSON to {clipped_states_path}")

    # --- Reload MSAs and clipped states as raw GeoJSON ---
    msa_geo: dict[str, Any]
    states_geo: dict[str, Any]

    with msa_path.open(encoding="utf-8") as f:
        msa_geo = json.load(f)
    with clipped_states_path.open(encoding="utf-8") as f:
        states_geo = json.load(f)

    # --- Normalize feature IDs ---
    LOGGER.info("Normalizing region_id fields...")
    for feat in msa_geo["features"]:
        feat["properties"]["region_id"] = feat["properties"]["CBSAFP"]

    for feat in states_geo["features"]:
        feat["properties"]["region_id"] = feat["properties"]["STATEFP"].lstrip("0")

    # --- Combine into FeatureCollection ---
    combined_geo: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": msa_geo["features"] + states_geo["features"],
    }
    LOGGER.info("Combined MSAs + States into a unified FeatureCollection.")

    # --- Write combined GeoJSON ---
    combined_path: Path = data_dir / combined_filename
    with combined_path.open("w", encoding="utf-8") as f:
        json.dump(combined_geo, f, ensure_ascii=False, indent=2)

    if not clipped_states_keep:
        clipped_states_path.unlink()  # remove temporary clipped states file

    LOGGER.info(
        f"Wrote {len(gdf_states_clipped) + len(gdf_msas_filtered)} "
        f"features to {combined_path}"
    )

    return None


def download_bea_gdp_percent_change(
    start_year: int = 2018,
    end_year: int = 2023,
    output_file: Path = GDP_FILE,
) -> pd.DataFrame | None:
    """Download BEA GDP data for all MSAs and calculate percent change.

    Args:
        start_year: First year to request.
        end_year: Last year to request.
        output_file: Destination CSV file.

    Returns:
        DataFrame of GDP percent changes or None on failure.
    """
    years: str = ",".join(str(y) for y in range(start_year, end_year + 1))

    params: dict[str, str] = {
        "UserID": API_KEY,
        "method": "GetData",
        "datasetname": "Regional",
        "TableName": "CAGDP1",
        "LineCode": "1",  # Real GDP (thousands of chained 2017 dollars)
        "Year": years,
        "GeoFips": "MSA",
        "ResultFormat": "json",
    }

    LOGGER.info(f"Requesting BEA GDP data ({start_year} - {end_year})...")

    try:
        response: requests.Response = requests.get(BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

    except Exception as exc:
        LOGGER.error("Error fetching BEA GDP data: %s", exc, exc_info=True)
        return None

    # --- Validate response ----------------------------------------------------
    try:
        results: dict[str, Any] = data["BEAAPI"]["Results"]
        rows: list[dict[str, Any]] = results.get("Data", [])
    except Exception:
        LOGGER.error("Unexpected BEA API response format.")
        return None

    if not rows:
        LOGGER.warning("No data returned from BEA API.")
        return None

    # --- Convert to DataFrame -------------------------------------------------
    rows_df: pd.DataFrame = pd.DataFrame(rows)
    rows_df["DataValue"] = pd.to_numeric(rows_df["DataValue"], errors="coerce")

    # --- Pivot from long → wide ----------------------------------------------
    pivot_df: pd.DataFrame = rows_df.pivot_table(
        index=["GeoFips", "GeoName"],
        columns="TimePeriod",
        values="DataValue",
        aggfunc="first",
    ).reset_index()

    # --- Compute percent changes ---------------------------------------------
    year_cols: list[Any] = sorted([c for c in pivot_df.columns if str(c).isdigit()])
    base_df: pd.DataFrame = pivot_df.copy()

    for i in range(1, len(year_cols)):
        curr, prev = year_cols[i], year_cols[i - 1]
        pivot_df[curr] = ((base_df[curr] - base_df[prev]) / base_df[prev] * 100).round(
            1
        )

    # Drop the first year (no percent change available)
    first_col: Any = year_cols[0]
    pivot_df = pivot_df.drop(columns=[first_col])

    # --- Save results ---------------------------------------------------------
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pivot_df.to_csv(output_file, index=False)
        LOGGER.info("GDP data saved to: %s", output_file.resolve())
    except Exception as exc:
        LOGGER.error("Failed to write GDP output file: %s", exc, exc_info=True)
        return None

    return pivot_df


def merge_healthcare_with_gdp(
    healthcare_path: Path,
    gdp_path: Path,
    output_path: Path,
) -> pd.DataFrame | None:
    """Merge BEA GDP percent-change with healthcare employment dataset."""
    LOGGER.info("Merging healthcare dataset with GDP dataset...")

    if not healthcare_path.exists():
        LOGGER.error("Healthcare dataset not found: %s", healthcare_path)
        return None

    if not gdp_path.exists():
        LOGGER.error("GDP dataset not found: %s", gdp_path)
        return None

    try:
        rise: pd.DataFrame = pd.read_csv(healthcare_path)
        gdp: pd.DataFrame = pd.read_csv(gdp_path)

        rise["metro13"] = pd.to_numeric(rise["metro13"], errors="coerce")
        gdp["GeoFips"] = pd.to_numeric(gdp["GeoFips"], errors="coerce")

        # keep only matching MSAs
        rise = rise[rise["metro13"].isin(gdp["GeoFips"])].copy()

        gdp = gdp.rename(
            columns={
                "2019": "gdp_growth_2019_percent",
                "2020": "gdp_growth_2020_percent",
                "2021": "gdp_growth_2021_percent",
                "2022": "gdp_growth_2022_percent",
                "2023": "gdp_growth_2023_percent",
            }
        )

        merged: pd.DataFrame = rise.merge(
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

        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output_path, index=False)

        LOGGER.info("Merged dataset saved at: %s", output_path.resolve())
        LOGGER.info(
            "Rows: %d | Columns: %d successfully merged.",
            len(merged),
            len(merged.columns),
        )

        return merged

    except Exception as exc:
        LOGGER.error("Error merging healthcare + GDP datasets: %s", exc, exc_info=True)
        return None
