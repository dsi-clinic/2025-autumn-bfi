"""Data preprocessing script to download, extract, and convert shapefiles to GeoJSON format, and prepare combined GeoJSON for US metropolitan areas and states.

url sources: United States Census Bureau
- CBSA shapefile: https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_cbsa_5m.zip
- State shapefile: https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip
"""

import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_cbsa_5m.zip"

r = requests.get(url, timeout=10)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("data/cb_2021_us_cbsa_5m")
z.close()

url2 = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip"

r2 = requests.get(url2, timeout=10)
z2 = zipfile.ZipFile(io.BytesIO(r2.content))
z2.extractall("data/cb_2021_us_state_5m")
z2.close()

# Convert extracted shapefiles to GeoJSON

datadf = pd.read_csv("data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv")
# Reshape df to long format
value_cols = [c for c in datadf.columns if c not in ["metro13", "metro_title"]]
df_long = datadf.melt(
    id_vars=["metro13", "metro_title"],
    value_vars=value_cols,
    var_name="indicator",
    value_name="value",
)

shp_dirs = {
    "cbsa": Path("data/cb_2021_us_cbsa_5m"),
    "states": Path("data/cb_2021_us_state_5m"),
}

out_paths = {
    "cbsa": Path("data/2021_US_CBSA_auto.geojson"),
    "states": Path("data/2021_US_States_auto.geojson"),
}

epsg_wgs84 = 4326

for key, d in shp_dirs.items():
    shp_files = sorted(d.glob("*.shp"))
    if not shp_files:
        print(f"No .shp found in {d!s}; skipping {key}")
        continue

    shp_path = shp_files[0]
    gdf = gpd.read_file(shp_path)

    # ensure WGS84 (GeoJSON-friendly)

    if gdf.crs is None or gdf.crs.to_epsg() != epsg_wgs84:
        gdf = gdf.to_crs(epsg=epsg_wgs84)

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
gdf_states = gpd.read_file("data/2021_US_States_auto.geojson")
gdf_msas = gpd.read_file("data/2021_US_CBSA_auto.geojson")

# --- Filter MSAs to only those you have data for
msa_ids_with_data = df_long["metro13"].astype(str).unique()
gdf_msas_data = gdf_msas[gdf_msas["CBSAFP"].astype(str).isin(msa_ids_with_data)]

# --- Clip states: remove only the MSAs that have data
gdf_states_clipped = gdf_states.overlay(gdf_msas_data, how="difference")

# --- Save for later use
gdf_states_clipped.to_file("data/2021_US_States_clipped_auto.geojson", driver="GeoJSON")

with Path.open("data/2021_US_CBSA_auto.geojson", encoding="utf-8") as f:
    msa_geo = json.load(f)
with Path.open("data/2021_US_States_clipped_auto.geojson", encoding="utf-8") as f:
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

output_path = Path("data/combined_US_regions_auto.geojson")

with output_path.open("w", encoding="utf-8") as f:
    json.dump(combined_geo, f, ensure_ascii=False, indent=2, default=str)
    print(
        f"Wrote {len(gdf_states_clipped) + len(gdf_msas_data)} features to {output_path}"
    )

print("Shapefile preprocessing complete!")
