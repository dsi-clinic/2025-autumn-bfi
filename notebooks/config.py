"""
Configuration file for MSA Dashboard
Contains all color palettes, data paths, styling constants, and chart/demographic relationships
"""
from typing import List, Tuple, Dict

# -------------------------
# Color Palettes
# -------------------------
PALETTES: List[List[str]] = [
    ["#800000", "#C5050C", "#FF5F05"],  # UChicago tones (maroon/red/orange)
    ["#005C99", "#0099CC", "#66CCFF"],  # Blues
    ["#1B5E20", "#43A047", "#A5D6A7"],  # Greens
]

COLOR_PALETTE: Dict[str, str] = {
    "healthcare": "#800000",      # maroon
    "population": "#005C99",      # deep blue
    "earnings": "#FF5F05",        # orange
    "college": "#1B5E20",         # green
    "manufacturing": "#9C27B0",   # purple
}

# -------------------------
# Data File Paths
# -------------------------
DATA_PATHS = [
    "../data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv"
]

CLEANED_PATHS = [
    "../data/Cleaned_data.csv"
]

MERGED_1980_PATHS = [
    "~/Downloads/merged_pop_1980.csv"
]

MIN_2022_PATHS = [
    "~/Downloads/min_df_2022.csv"
]

GDP_PATHS = [
    "../data/merged_healthcare_jobs_with_gdp.csv"
]

# -------------------------
# Chart Relationships
# -------------------------
RELATIONSHIPS: List[Tuple[str, str, str, str, List[str]]] = [
    ("change_ln_population", "hc_emp_share_prime_change",
     "Change in Population (log)", "Change in Healthcare Employment Share", PALETTES[0]),

    ("change_earnings", "hc_emp_share_prime_change",
     "Change in Earnings", "Change in Healthcare Employment Share", PALETTES[0]),

    ("change_college", "hc_emp_share_prime_change",
     "Change in College Share", "Change in Healthcare Employment Share", PALETTES[1]),

    ("manu_share_prime_change", "hc_emp_share_prime_change",
     "Change in Manufacturing Share", "Change in Healthcare Employment Share", PALETTES[1]),

    ("change_medicare_share", "hc_emp_share_prime_change",
     "Change in Medicare Share", "Change in Healthcare Employment Share", PALETTES[2]),

    ("change_non_hc_share_lbfr", "hc_emp_share_prime_change",
     "Change in Non-Healthcare Labor Force Participation Rate (LFPR)",
     "Change in Healthcare Employment Share", PALETTES[2]),
]

GDP_RELATIONSHIPS: List[Tuple[str, str, str, str, str]] = [
    ("gdp_growth_2021_percent", "hc_emp_share_prime_change",
     "GDP Growth (2021, %)", "Healthcare Employment Share Change", COLOR_PALETTE["healthcare"]),

    ("gdp_growth_2021_percent", "change_ln_population",
     "GDP Growth (2021, %)", "Population Growth (log)", COLOR_PALETTE["population"]),

    ("gdp_growth_2021_percent", "change_earnings",
     "GDP Growth (2021, %)", "Earnings Change", COLOR_PALETTE["earnings"]),

    ("gdp_growth_2021_percent", "change_college",
     "GDP Growth (2021, %)", "College Share Change", COLOR_PALETTE["college"]),

    ("gdp_growth_2021_percent", "manu_share_prime_change",
     "GDP Growth (2021, %)", "Manufacturing Share Change", COLOR_PALETTE["manufacturing"]),
]

# -------------------------
# Streamlit Page Config
# -------------------------
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "MSA Dashboard"
}

# -------------------------
# Custom CSS Styling
# -------------------------
CUSTOM_CSS = """
    <style>
    .stApp .css-18e3th9 {
        padding-top: 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
        text-align: center !important;
        margin: 0.2rem 0 0.6rem 0;
    }
    p, div, span {
        color: white !important;
    }
    .center-caption {
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-bottom: 0.75rem;
    }
    .logo-col img {
        display: block;
        margin-left: 0;
    }
    </style>
"""

# -------------------------
# Demographics Categories
# -------------------------
DEMOGRAPHIC_CATEGORIES = [
    "White male",
    "Black male",
    "Other races male",
    "White female",
    "Black female",
    "Other races female",
]

DEMOGRAPHIC_AGG_COLS = [
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
