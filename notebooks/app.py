import os
import logging
from typing import List, Tuple, Dict

import streamlit as st
import pandas as pd
import altair as alt
alt.data_transformers.disable_max_rows()
from sklearn.linear_model import LinearRegression

# -------------------------
# Config / Logging
# -------------------------
st.set_page_config(layout="wide", page_title="MSA Dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -------------------------
# Styling (maroon + centered headings)
# -------------------------
st.markdown(
    """
    <style>
    .stApp .css-18e3th9 {  /* main container padding adjustments (Streamlit class may vary by version) */
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
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Helper: try multiple paths for data files
# -------------------------
def try_read_csv(possible_paths: List[str], file_label: str = "file"):
    for p in possible_paths:
        try:
            p_expanded = os.path.expanduser(p)
            if os.path.exists(p_expanded):
                df = pd.read_csv(p_expanded)
                logging.info(f"Loaded {file_label} from {p_expanded}")
                return df
        except Exception as e:
            logging.warning(f"Failed to read {p} ({e})")
    st.error(f"Could not locate {file_label}. Tried: {possible_paths}")
    return None

# -------------------------
# Header with title
# -------------------------
st.markdown("<h1>Interactive Maps of MSA's</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color: white;'>Understanding the socioeconomic and demographic factors behind healthcare employment growth across U.S. MSAs (1980–2022).</p>",
    unsafe_allow_html=True,
)
# -------------------------
# Data file paths 
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
# Load data (graceful errors shown in app)
# -------------------------
df = try_read_csv(DATA_PATHS, "main MSA dataset")
cleaned_data = try_read_csv(CLEANED_PATHS, "cleaned dataset (for chart 6)")
merged_pop_1980 = try_read_csv(MERGED_1980_PATHS, "merged_pop_1980 (1980 population)")
min_df_2022 = try_read_csv(MIN_2022_PATHS, "min_df_2022 (2022 population)")

# If main df missing, stop early
if df is None:
    st.stop()

# Trim original notebook slicing if present
try:
    df = df.iloc[33:].reset_index(drop=True)
except Exception:
    # keep df as-is if slicing fails
    pass

# -------------------------
# Palettes & relationships 
# -------------------------
PALETTES: List[List[str]] = [
    ["#800000", "#C5050C", "#FF5F05"],  # UChicago tones
    ["#005C99", "#0099CC", "#66CCFF"],  # Blues
    ["#1B5E20", "#43A047", "#A5D6A7"],  # Greens
]

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

# -------------------------
# Regression helper
# -------------------------
def compute_regression_stats(df: pd.DataFrame, x: str, y: str) -> str:
    """Return slope and R² as formatted string."""
    try:
        model = LinearRegression()
        x_vals = df[[x]].dropna()
        y_vals = df[y].dropna()
        # align indices
        y_aligned = y_vals.loc[x_vals.index]
        if len(x_vals) == 0 or len(y_aligned) == 0:
            return "Regression unavailable"
        model.fit(x_vals, y_aligned)
        r2 = model.score(x_vals, y_aligned)
        slope = model.coef_[0]
        return f"Slope={slope:.2f}, R²={r2:.2f}"
    except Exception as e:
        logging.warning(f"Could not compute regression stats for {x} vs {y}: {e}")
        return "Regression unavailable"

# -------------------------
# Chart creator
# -------------------------
def make_colored_reg_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    x_label: str,
    y_label: str,
    palette: List[str],
) -> alt.Chart:
    """
    Create an Altair scatterplot with regression line and tooltip + stats.
    """
    logging.info(f"Building chart: {y_label} vs {x_label}")

    base = alt.Chart(df).encode(
        x=alt.X(x, title=x_label, axis=alt.Axis(labelFontSize=11, titleFontSize=12)),
        y=alt.Y(y, title=y_label, axis=alt.Axis(labelFontSize=11, titleFontSize=12)),
    )

    points = base.mark_circle(size=80, opacity=0.75, color=palette[0]).encode(
        tooltip=[
            alt.Tooltip("metro_title:N", title="MSA"),
            alt.Tooltip(x, title=x_label, format=".2%"),
            alt.Tooltip(y, title=y_label, format=".2%"),
        ]
    )

    # regression line (Altair transform_regression)
    regression = base.transform_regression(x, y, method="linear").mark_line(
        color=palette[1], size=2.5
    )

    # regression stats text
    stats_label = compute_regression_stats(df, x, y)
    stats_text = (
        alt.Chart(pd.DataFrame({"text": [stats_label]}))
        .mark_text(align="left", x=10, y=15, fontSize=10, color="black")
        .encode(text="text:N")
    )

    chart = (points + regression + stats_text).properties(
        width=340, height=330, title=f"{y_label} vs {x_label}"
    )

    return chart

# -------------------------
# Build dashboard (2x3)
# -------------------------
def build_dashboard(df: pd.DataFrame, relationships: List[Tuple]) -> alt.VConcatChart:
    charts = [make_colored_reg_chart(df, *r) for r in relationships]

    # arrange into two rows
    row1 = charts[0] | charts[1] | charts[2]
    row2 = charts[3] | charts[4] | charts[5]
    dashboard = (row1 & row2).properties(title="MSA-Level Economic Relationships (1980–2022)")

    dashboard = (
        dashboard.configure_title(fontSize=18, anchor="middle")
        .configure_axis(labelFontSize=11, titleFontSize=12, grid=True)
        .configure_view(strokeWidth=0)
    )
    logging.info("Dashboard created")
    return dashboard

# -------------------------
# Render new dashboard (replacing old supplementary charts)
# -------------------------
st.markdown("<h3>Supplementary Charts</h3>", unsafe_allow_html=True)
st.markdown(
    "<p class='center-caption'>These supplementary charts provide additional context for understanding relationships between population, education, earnings, and healthcare employment growth across MSAs.</p>",
    unsafe_allow_html=True,
)

# Build individual charts
charts = [make_colored_reg_chart(df, *r) for r in RELATIONSHIPS]

# Render in a 2x3 grid using Streamlit columns
col1, col2, col3 = st.columns(3)
with col1:
    st.altair_chart(charts[0], use_container_width=True)
with col2:
    st.altair_chart(charts[1], use_container_width=True)
with col3:
    st.altair_chart(charts[2], use_container_width=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.altair_chart(charts[3], use_container_width=True)
with col5:
    st.altair_chart(charts[4], use_container_width=True)
with col6:
    st.altair_chart(charts[5], use_container_width=True)


# ==============================================================
# Additional Supplementary Charts — GDP Relationships (2021)
# ==============================================================

# -------------------------
# GDP Relationship Dashboard
# -------------------------
df_gdp = try_read_csv(GDP_PATHS, "GDP dataset")
if df_gdp is not None:
    st.markdown("<h3>GDP Growth Relationships (2021)</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p class='center-caption'>Explore how GDP growth in 2021 relates to key economic indicators across MSAs.</p>",
        unsafe_allow_html=True,
    )
    COLOR_PALETTE: Dict[str, str] = {
    "healthcare": "#800000",      # maroon
    "population": "#005C99",      # deep blue
    "earnings": "#FF5F05",        # orange
    "college": "#1B5E20",         # green
    "manufacturing": "#9C27B0",   # purple
    }

    # ---- GDP scatter chart builder ----
    def make_scatter_chart(data, x, y, x_label, y_label, color):
        base = alt.Chart(data).encode(
            x=alt.X(x, title=x_label, axis=alt.Axis(labelFontSize=11, titleFontSize=12)),
            y=alt.Y(y, title=y_label, axis=alt.Axis(labelFontSize=11, titleFontSize=12)),
        )

        scatter = base.mark_circle(size=80, opacity=0.7, color=color).encode(
            tooltip=[
                alt.Tooltip("metro_title:N", title="MSA"),
                alt.Tooltip(x, title=x_label, format=".2f"),
                alt.Tooltip(y, title=y_label, format=".2f"),
            ]
        )

        regression = base.transform_regression(x, y).mark_line(color="black", strokeWidth=2)

        return (scatter + regression).properties(
            width=330,
            height=400,  # Made taller to match supplementary charts
            title=f"{y_label} vs {x_label}",
        )

    # ---- Build GDP relationship charts ----
    relationships = [
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

    # Build individual charts
    gdp_charts = [make_scatter_chart(df_gdp, *r) for r in relationships]

    # ---- Render GDP Charts in Grid Layout ----
    # First row: 3 charts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.altair_chart(gdp_charts[0], use_container_width=True)
    with col2:
        st.altair_chart(gdp_charts[1], use_container_width=True)
    with col3:
        st.altair_chart(gdp_charts[2], use_container_width=True)

    # Second row: 2 charts
    col4, col5 = st.columns(2)
    with col4:
        st.altair_chart(gdp_charts[3], use_container_width=True)
    with col5:
        st.altair_chart(gdp_charts[4], use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

else:
    st.warning("GDP dataset not found. Supplementary GDP charts unavailable.")


# -------------------------
# Interactive MSA Demographics (1980 & 2022)
# -------------------------
# If merged_pop_1980 or min_df_2022 missing, show warnings and skip this block gracefully
if merged_pop_1980 is None or min_df_2022 is None:
    st.warning("1980/2022 population detail files not found. Skipping the demographics comparison section. Place files in Downloads or ../data and reload.")
else:
    # Prepare 1980 tables
    cats = [
        "White male",
        "Black male",
        "Other races male",
        "White female",
        "Black female",
        "Other races female",
    ]

    agg = merged_pop_1980.groupby(["metro_title", "Race/Sex Indicator"], as_index=False)["Total Population"].sum()
    msa_tables_1980 = {}
    for msa, g in agg.groupby("metro_title", sort=True):
        p = g.pivot_table(index="Race/Sex Indicator", values="Total Population", aggfunc="sum", fill_value=0).reindex(cats)

        male_total = p.loc[["White male", "Black male", "Other races male"]].sum().item()
        male_white = 0 if male_total == 0 else p.loc["White male"].item() / male_total * 100
        male_black = 0 if male_total == 0 else p.loc["Black male"].item() / male_total * 100
        male_other = 0 if male_total == 0 else p.loc["Other races male"].item() / male_total * 100

        female_total = p.loc[["White female", "Black female", "Other races female"]].sum().item()
        female_white = 0 if female_total == 0 else p.loc["White female"].item() / female_total * 100
        female_black = 0 if female_total == 0 else p.loc["Black female"].item() / female_total * 100
        female_other = 0 if female_total == 0 else p.loc["Other races female"].item() / female_total * 100

        proportions = pd.DataFrame(
            {
                "White": [male_white, female_white],
                "Black": [male_black, female_black],
                "Other": [male_other, female_other],
            },
            index=["Male", "Female"],
        ).round(2)
        msa_tables_1980[msa] = proportions

    # Prepare 2022 tables
    msa_tables_2022 = {}
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
    msa_totals = min_df_2022.groupby("metro_title", as_index=False)[agg_cols].sum()

    male_props = msa_totals[["metro_title", "WAC_MALE", "BAC_MALE", "OTHER_MALE", "TOT_MALE"]].copy()
    male_props[["White", "Black", "Other"]] = male_props[["WAC_MALE", "BAC_MALE", "OTHER_MALE"]].div(male_props["TOT_MALE"], axis=0)
    male_props = male_props[["metro_title", "White", "Black", "Other"]]

    female_props = msa_totals[["metro_title", "WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE", "TOT_FEMALE"]].copy()
    female_props[["White", "Black", "Other"]] = female_props[["WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE"]].div(female_props["TOT_FEMALE"], axis=0)
    female_props = female_props[["metro_title", "White", "Black", "Other"]]

    for msa in msa_totals["metro_title"]:
        male_row = male_props.loc[male_props["metro_title"] == msa, ["White", "Black", "Other"]].squeeze()
        female_row = female_props.loc[female_props["metro_title"] == msa, ["White", "Black", "Other"]].squeeze()

        proportions = pd.DataFrame([male_row.to_numpy(), female_row.to_numpy()], index=["Male", "Female"], columns=["White", "Black", "Other"]).astype(float)
        proportions = (proportions * 100).round(2)
        msa_tables_2022[msa] = proportions

    # Shared dropdown 
    common_msas = sorted(set(msa_tables_1980.keys()) & set(msa_tables_2022.keys()))
    selected_msa_compare = st.selectbox("Select a Metropolitan Statistical Area (MSA):", common_msas, index=0)

    st.markdown("<h3>Population Distribution by Race and Sex (1980 vs 2022)</h3>", unsafe_allow_html=True)
    st.markdown("<p class='center-caption'>Compare Male/Female racial shares side-by-side for the selected MSA.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### {selected_msa_compare} — 1980", unsafe_allow_html=True)
        st.dataframe(msa_tables_1980[selected_msa_compare])

    with col2:
        st.markdown(f"#### {selected_msa_compare} — 2022", unsafe_allow_html=True)
        st.dataframe(msa_tables_2022[selected_msa_compare])

    # Compact grouped bar chart (4 groups: Male(1980), Male(2022), Female(1980), Female(2022))
    chart_df_1980 = msa_tables_1980[selected_msa_compare].reset_index().melt(id_vars="index", var_name="Race", value_name="Percentage")
    chart_df_1980["Year"] = "1980"
    chart_df_2022 = msa_tables_2022[selected_msa_compare].reset_index().melt(id_vars="index", var_name="Race", value_name="Percentage")
    chart_df_2022["Year"] = "2022"
    combined_df = pd.concat([chart_df_1980, chart_df_2022]).rename(columns={"index": "Gender"})
    combined_df = combined_df[combined_df["Race"].isin(["White", "Black"])]  # keep two races for clarity

    combined_df["Group"] = combined_df["Gender"] + " (" + combined_df["Year"] + ")"

    bar_chart_compare = (
        alt.Chart(combined_df)
        .mark_bar(size=28)
        .encode(
            x=alt.X("Group:N", title=None, axis=alt.Axis(labelFontSize=12)),
            y=alt.Y("Percentage:Q", title="Percentage"),
            color=alt.Color("Race:N", scale=alt.Scale(range=["#ecd2c2", "#800000"]), legend=alt.Legend(title="Race")),
            tooltip=["Gender", "Year", "Race", "Percentage"]
        )
        .properties(width=480, height=320)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(bar_chart_compare, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)
