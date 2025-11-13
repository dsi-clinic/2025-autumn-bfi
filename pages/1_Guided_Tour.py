"""Guided Tour Page - Curated charts"""

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
if st.button("Go back Home"):
    st.switch_page("Homepage.py")
st.title("Interactive Maps of MSA's")

# === chart title styling ===
alt.themes.enable("none")
alt.themes.register(
    "compact_titles",
    lambda: {
        "config": {
            "title": {"fontSize": 12, "anchor": "middle", "fontWeight": "normal"}
        }
    },
)
alt.themes.enable("compact_titles")

# === Load main dataset ===
datadf = pd.read_csv("data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv")
# everything before 33 are states, we are focusing on MSA's
datadf = datadf.iloc[33:].reset_index(drop=True)
cleaned_data = pd.read_csv("~/Downloads/Cleaned_data.csv")


# === Define Supplementary Charts ===
def chart1(df: pd.DataFrame = datadf) -> alt.Chart:
    """Chart 1: Top 10 MSAs by Healthcare Employment Share (2022)

    df: Dataframe to use for the chart. Default is datadf.
    Returns: Altair Chart object.
    """
    top10 = df.nlargest(10, "healthcare_share_prime2022").copy()
    c = (
        alt.Chart(top10)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            y=alt.Y(
                "metro_title:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelFontSize=10, labelLimit=200),
            ),
            x=alt.X(
                "healthcare_share_prime2022:Q",
                title="Healthcare Employment Share (2022)",
                axis=alt.Axis(format=".0%", labelFontSize=12, titleFontSize=14),
            ),
            color=alt.Color(
                "healthcare_share_prime2022:Q",
                scale=alt.Scale(range=["#ecd2c2", "#a05252", "#800000"]),
                legend=None,
            ),
            tooltip=["metro_title", "healthcare_share_prime2022"],
        )
        .properties(
            width=450,
            height=320,
            title="Top 10 MSAs by Healthcare Employment Share (2022)",
        )
    )
    return c


def chart2(df: pd.DataFrame = datadf) -> alt.Chart:
    """Chart 2: Top 10 MSAs by Increase in Healthcare Employment Share (1980–2022)

    df: Dataframe to use for the chart. Default is datadf.
    Returns: Altair Chart object.
    """
    top10 = df.nlargest(10, "hc_emp_share_prime_change").copy()
    top10["zero"] = 0
    base = alt.Chart(top10).encode(
        x=alt.X(
            "metro_title:N",
            sort="-y",
            axis=alt.Axis(labelAngle=-30, labelFontSize=10, labelLimit=250),
        ),
        y=alt.Y(
            "hc_emp_share_prime_change:Q",
            title="Increase in Healthcare Employment Share (1980–2022)",
            axis=alt.Axis(format=".1%", labelFontSize=11, titleFontSize=13),
        ),
    )
    stems = base.mark_rule(stroke="#a05252", strokeWidth=2).encode(
        y="zero:Q", y2="hc_emp_share_prime_change:Q"
    )
    dots = base.mark_circle(size=80, color="#800000").encode()
    chart = (stems + dots).properties(
        width=450, height=320, title="Top 10 MSAs by Healthcare Job Growth"
    )
    return chart


def chart3(df: pd.DataFrame = datadf) -> alt.Chart:
    """Chart 3: Manufacturing vs Healthcare Employment Change

    df: Dataframe to use for the chart. Default is datadf.
    Returns: Altair Chart object.
    """
    c = (
        alt.Chart(df)
        .mark_circle(size=80, color="#800000", opacity=0.8)
        .encode(
            x=alt.X(
                "manu_share_prime_change:Q",
                title="Change in Manufacturing Employment Share (1980–2022)",
                axis=alt.Axis(format=".1%", labelFontSize=11),
            ),
            y=alt.Y(
                "hc_emp_share_prime_change:Q",
                title="Change in Healthcare Employment Share (1980–2022)",
                axis=alt.Axis(format=".1%", labelFontSize=11),
            ),
            tooltip=[
                "metro_title",
                "hc_emp_share_prime_change",
                "manu_share_prime_change",
            ],
        )
        .properties(
            width=450, height=320, title="Healthcare vs Manufacturing Employment Change"
        )
    )
    return c


def chart4(df: pd.DataFrame = datadf) -> alt.Chart:
    """Chart 4: Education vs Healthcare Employment Growth

    df: Dataframe to use for the chart. Default is datadf.
    Returns: Altair Chart object.
    """
    c = (
        alt.Chart(df)
        .mark_circle(size=80, color="#1E88E5", opacity=0.75)
        .encode(
            x=alt.X(
                "change_college:Q",
                title="Change in % College Educated (1980–2022)",
                axis=alt.Axis(format=".1%", labelFontSize=11),
            ),
            y=alt.Y(
                "hc_emp_share_prime_change:Q",
                title="Change in Healthcare Employment Share (1980–2022)",
                axis=alt.Axis(format=".1%", labelFontSize=11),
            ),
            tooltip=["metro_title", "change_college", "hc_emp_share_prime_change"],
        )
        .properties(
            width=450,
            height=320,
            title="College Education vs Healthcare Employment Change",
        )
    )
    return c


def chart5(df: pd.DataFrame = datadf) -> alt.Chart:
    """Chart 5: Earnings Growth vs Healthcare Employment Growth

    df: Dataframe to use for the chart. Default is datadf.
    Returns: Altair Chart object.
    """
    c = (
        alt.Chart(df)
        .mark_circle(opacity=0.7)
        .encode(
            x="change_earnings:Q",
            y="hc_emp_share_prime_change:Q",
            size=alt.Size(
                "ln_msa_pop2022:Q",
                legend=alt.Legend(
                    title="Population (log scale)",
                    labelFontSize=9,
                    titleFontSize=10,
                    symbolSize=40,
                ),
            ),
            color=alt.value("#004B87"),
            tooltip=[
                "metro_title",
                "change_earnings",
                "hc_emp_share_prime_change",
                "ln_msa_pop2022",
            ],
        )
        .properties(
            title="Earnings Growth vs Healthcare Employment Growth",
            width=450,
            height=320,
        )
    )
    return c


def chart6(df: pd.DataFrame = cleaned_data) -> alt.Chart:
    """Chart 6: Debt-to-Income vs Healthcare Employment Share

    df: Dataframe to use for the chart. Default is cleaned_data.
    Returns: Altair Chart object.
    """
    c = (
        alt.Chart(df)
        .mark_circle(size=80, color="#800000", opacity=0.75)
        .encode(
            x=alt.X(
                "AverageDTI:Q",
                title="Average Debt-to-Income Ratio (Q4 2022)",
                axis=alt.Axis(format=".0%", labelFontSize=11),
            ),
            y=alt.Y(
                "healthcare_share_prime2022:Q",
                title="Healthcare Employment Share (2022)",
                axis=alt.Axis(format=".0%", labelFontSize=11),
            ),
            tooltip=["metro_title", "AverageDTI", "healthcare_share_prime2022"],
        )
        .properties(
            title="Debt-to-Income vs Healthcare Employment Share", width=450, height=350
        )
    )
    return c


# === Display Charts ===
st.write("### Supplementary Charts")

# First three charts
cols1 = st.columns([1, 1, 1], gap="large")
charts_row1 = [chart1(), chart2(), chart3()]
descriptions_row1 = [
    "Top 10 MSAs ranked by healthcare employment share in 2022",
    "Top 10 MSA's with the largest increase in healthcare job share from 1980–2022",
    "Change in manufacturing and healthcare employment change across MSA's",
]

for i, col in enumerate(cols1):
    with col:
        st.altair_chart(charts_row1[i], use_container_width=True)
        st.caption(descriptions_row1[i])

st.markdown("<br><br>", unsafe_allow_html=True)

# Second row with three charts
cols2 = st.columns([1, 1, 1], gap="large")
charts_row2 = [chart4(), chart5(), chart6()]
descriptions_row2 = [
    "Correlation between education levels and healthcare job growth",
    "Comparison of earnings growth with healthcare job growth",
    "Healthcare job share compared to average household debt-to-income ratios",
]

for i, col in enumerate(cols2):
    with col:
        st.altair_chart(charts_row2[i], use_container_width=True)
        st.caption(descriptions_row2[i])

st.markdown("<br><hr><br>", unsafe_allow_html=True)
