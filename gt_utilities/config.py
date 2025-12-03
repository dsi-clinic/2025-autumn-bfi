"""Configuration file for MSA Dashboard

Contains all color palettes, data paths, styling constants, and chart/demographic relationships
"""

from pathlib import Path

from gt_utilities import find_project_root

# -------------------------
# Color Palettes
# -------------------------
PALETTES: list[list[str]] = [
    ["#800000", "#C5050C", "#FF5F05"],  # UChicago tones (maroon/red/orange)
    ["#005C99", "#0099CC", "#66CCFF"],  # Blues
    ["#1B5E20", "#43A047", "#A5D6A7"],  # Greens
]

COLOR_PALETTE: dict[str, str] = {
    "healthcare": "#800000",  # maroon
    "population": "#005C99",  # deep blue
    "earnings": "#FF5F05",  # orange
    "college": "#1B5E20",  # green
    "manufacturing": "#9C27B0",  # purple
}

# -------------------------
# Data File Paths and Environmental Variables
# -------------------------
PROJECT_ROOT: Path = find_project_root()
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATHS: Path = DATA_DIR / "the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
GDP_PATHS: Path = DATA_DIR / "merged_healthcare_jobs_with_gdp.csv"
MERGED_PATHS: Path = DATA_DIR / "merged_bfi.csv"

COMBINED_GEOJSON: Path = DATA_DIR / "combined_US_regions_auto.geojson"
GDP_FILE = DATA_DIR / "msa_gdp_percent_change.csv"

API_KEY: str = "73110DFA-D36D-4A7C-99C7-183B704E1596"
BASE_URL: str = "https://apps.bea.gov/api/data"
GDP_FILE: Path = DATA_DIR / "msa_gdp_percent_change.csv"
MERGED_FILE: Path = DATA_DIR / "merged_healthcare_jobs_with_gdp.csv"

# --------------------------
# Resource urls for Raw Data
# --------------------------
# Make raw data urls hyper-parameters within dictionaries
RAW_CENSUS_POP_DATA_URLS = {
    "https://www2.census.gov/programs-surveys/popest/datasets/"
    "1980-1990/counties/asrh/pe-02.csv": "1980",
    "https://www2.census.gov/programs-surveys/popest/datasets/"
    "2020-2023/metro/asrh/cbsa-est2023-alldata-char.csv": "2022",
}

UBLA_LABOR_DATA_ZIP_URLS_AND_RAW_PATHS = {
    "https://data.bls.gov/cew/data/files/1980/sic/csv/"
    "sic_1980_annual_by_industry.zip": "sic.1980.annual.by_industry/"
    "sic.1980.annual 0Z (All Industries).csv",
    "https://data.bls.gov/cew/data/files/2022/csv/"
    "2022_annual_by_industry.zip": "2022.annual.by_industry/"
    "2022.annual 10 10 Total, all industries.csv",
}

NBER_COUNTY_CBSA_CROSSWALK_URL = (
    "https://data.nber.org/cbsa-csa-fips-county-crosswalk/cbsa2fipsxw.csv"
)

# -------------------------
# Chart Relationships
# -------------------------
RELATIONSHIPS: list[tuple[str, str, str, str, list[str]]] = [
    (
        "change_ln_population",
        "hc_emp_share_prime_change",
        "Change in Population (log)",
        "Change in Healthcare Employment Share",
        PALETTES[0],
    ),
    (
        "change_earnings",
        "hc_emp_share_prime_change",
        "Change in Earnings",
        "Change in Healthcare Employment Share",
        PALETTES[0],
    ),
    (
        "change_college",
        "hc_emp_share_prime_change",
        "Change in College Share",
        "Change in Healthcare Employment Share",
        PALETTES[1],
    ),
    (
        "manu_share_prime_change",
        "hc_emp_share_prime_change",
        "Change in Manufacturing Share",
        "Change in Healthcare Employment Share",
        PALETTES[1],
    ),
    (
        "change_medicare_share",
        "hc_emp_share_prime_change",
        "Change in Medicare Share",
        "Change in Healthcare Employment Share",
        PALETTES[2],
    ),
    (
        "change_non_hc_share_lbfr",
        "hc_emp_share_prime_change",
        "Change in Non-Healthcare Labor Force Participation Rate (LFPR)",
        "Change in Healthcare Employment Share",
        PALETTES[2],
    ),
]

GDP_RELATIONSHIPS: list[tuple[str, str, str, str, str]] = [
    (
        "hc_emp_share_prime_change",
        "gdp_growth_2021_percent",
        "Healthcare Employment Share Change",
        "GDP Growth (2021, %)",
        COLOR_PALETTE["healthcare"],
    ),
    (
        "change_ln_population",
        "gdp_growth_2021_percent",
        "Population Growth (log)",
        "GDP Growth (2021, %)",
        COLOR_PALETTE["population"],
    ),
    (
        "change_earnings",
        "gdp_growth_2021_percent",
        "Earnings Change",
        "GDP Growth (2021, %)",
        COLOR_PALETTE["earnings"],
    ),
    (
        "change_college",
        "gdp_growth_2021_percent",
        "College Share Change",
        "GDP Growth (2021, %)",
        COLOR_PALETTE["college"],
    ),
    (
        "manu_share_prime_change",
        "gdp_growth_2021_percent",
        "Manufacturing Share Change",
        "GDP Growth (2021, %)",
        COLOR_PALETTE["manufacturing"],
    ),
]

# -------------------------
# Streamlit Page Config
# -------------------------
PAGE_CONFIG: dict[str, str] = {"layout": "wide", "page_title": "MSA Dashboard"}

# -------------------------
# Custom CSS Styling (Apply as needed)
# -------------------------
# CUSTOM_CSS: str = """
#     <style>
#     .stApp .css-18e3th9 {
#         padding-top: 1rem;
#     }
#     h1, h2, h3, h4, h5, h6 {
#         color: white !important;
#         text-align: center !important;
#         margin: 0.2rem 0 0.6rem 0;
#     }
#     p, div, span {
#         color: white !important;
#     }
#     .center-caption {
#         color: rgba(255,255,255,0.9);
#         text-align: center;
#         margin-bottom: 0.75rem;
#     }
#     .logo-col img {
#         display: block;
#         margin-left: 0;
#     }
#     </style>
# """

# -------------------------
# Demographics Categories
# -------------------------
DEMOGRAPHIC_CATEGORIES: list[str] = [
    "TOT_POP",
    "TOT_MALE",
    "TOT_FEMALE",
    "white male",
    "black male",
    "other races male",
    "white female",
    "black female",
    "other races female",
]

DEMOGRAPHIC_AGG_COLS: list[str] = [
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

# -------------------------
# Variable Name Map for Display
# -------------------------
VARIABLE_NAME_MAP = {
    "ln_msa_pop1980": "Log Population (1980)",
    "ln_msa_pop2022": "Log Population (2022)",
    "change_ln_population": "Change in Log Population (1980–2022)",
    "change_ln_non_hc": "Change in Log Non-Healthcare Employment (1980–2022)",
    "change_non_hc_share_lbfr": "Change in Non-Healthcare Labor Force Share (1980–2022)",
    "healthcare_share_prime1980": "Prime-Age Healthcare Share (1980)",
    "healthcare_share_prime2022": "Prime-Age Healthcare Share (2022)",
    "hc_emp_share_prime_change": "Change in Prime-Age Healthcare Employment Share (1980–2022)",
    "manufacturing_share_prime1980": "Prime-Age Manufacturing Share (1980)",
    "manu_share_prime_change": "Change in Prime-Age Manufacturing Share (1980–2022)",
    "non_hc_share_prime_change": "Change in Non-Healthcare Prime-Age Employment Share (1980–2022)",
    "not_lbfr_share_prime_change": "Change in Prime-Age Not-in-Labor-Force Share (1980–2022)",
    "unemployed_share_prime_change": "Change in Prime-Age Unemployment Share (1980–2022)",
    "non_hc_manu_share_prime_change": "Change in Prime-Age Non-Healthcare & Non-Manufacturing Employment Share (1980–2022)",
    "non_manu_share_prime_change": "Change in Prime-Age Non-Manufacturing Share (1980–2022)",
    "medicare_share1980": "Medicare Share (1980)",
    "medicare_share2022": "Medicare Share (2022)",
    "change_medicare_share": "Change in Medicare Share (1980–2022)",
    "ln_aearn1980": "Log Average Earnings (1980)",
    "ln_aearn2022": "Log Average Earnings (2022)",
    "change_earnings": "Change in Log Average Earnings (1980–2022)",
    "college1980": "College Degree Share (1980)",
    "college2022": "College Degree Share (2022)",
    "change_college": "Change in College Degree Share (1980–2022)",
}

# --------------------------
# Chart Color Scales
# --------------------------

CHART_COLOR_SCALE: list = ["#ecd2c2", "#a05252", "#800000"]
