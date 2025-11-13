"""cleans supp data, creates tables of supp data, and merges them with bfi data

includes supp data for 1980 and 2022 population and employment info
"""

# %%
import pandas as pd

# %% [markdown]
# # Population (race, sex, age)

# %% [markdown]
# ## 1980

# %% [markdown]
# ### data wrangling

# %%
pop = pd.read_csv(
    "../../data/pop_1980.csv", skiprows=5, header=0
)  # first couple rows are informational text about csv
pop = pop.drop(0)  # first row empty
print(pop)

# %%
pop_1980 = pop.query("`Year of Estimate` == 1980")
print(pop_1980)

# %%
# add total population column
cols_to_sum = list(pop_1980.columns)[3:]
pop_1980["Total Population"] = pop_1980[cols_to_sum].sum(axis=1)
print(pop_1980.head())

# %%
chic = pop_1980.query("`FIPS State and County Codes` == 17031")
print(chic)

# %%
# only include msas in BFI dataset
bfi_df = pd.read_csv("../../data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv")
bfi_df.head()

# %%
# map county to msa
msa_county = pd.read_csv("../../data/cbsatocountycrosswalk.csv", encoding="latin1")
print(msa_county)

# %%
# add msa codes to each county
msa_pop_1980 = pop_1980.merge(
    msa_county[["ssacounty", "fipscounty", "cbsaname"]],
    left_on="FIPS State and County Codes",
    right_on="fipscounty",
    how="inner",
).drop(columns=["fipscounty"])
print(msa_pop_1980)

# %%
# keep only rows relevant to bfi dataset
merged_pop_1980 = msa_pop_1980.merge(
    bfi_df[["metro13", "metro_title"]],
    left_on="ssacounty",
    right_on="metro13",
    how="inner",
).drop(columns=["ssacounty", "cbsaname"])
print(merged_pop_1980)

# %%
# table of total populations per msa
total_pop = merged_pop_1980.groupby(["metro13", "metro_title"], as_index=False)[
    "Total Population"
].sum()
total_pop = total_pop.rename(columns={"Total Population": "MSA Population"})
print(total_pop.head())

# %%
msa_tables_1980 = {}

cats = [
    "White male",
    "Black male",
    "Other races male",
    "White female",
    "Black female",
    "Other races female",
]

agg = merged_pop_1980.groupby(["metro_title", "Race/Sex Indicator"], as_index=False)[
    "Total Population"
].sum()

for msa, g in agg.groupby("metro_title", sort=True):
    p = g.pivot_table(
        index="Race/Sex Indicator",
        values="Total Population",
        aggfunc="sum",
        fill_value=0,
    ).reindex(cats)

    # male totals & shares
    male_total = p.loc[["White male", "Black male", "Other races male"]].sum().item()
    male_white = 0 if male_total == 0 else p.loc["White male"].item() / male_total * 100
    male_black = 0 if male_total == 0 else p.loc["Black male"].item() / male_total * 100
    male_other = (
        0 if male_total == 0 else p.loc["Other races male"].item() / male_total * 100
    )

    # female totals & shares
    female_total = (
        p.loc[["White female", "Black female", "Other races female"]].sum().item()
    )
    female_white = (
        0 if female_total == 0 else p.loc["White female"].item() / female_total * 100
    )
    female_black = (
        0 if female_total == 0 else p.loc["Black female"].item() / female_total * 100
    )
    female_other = (
        0
        if female_total == 0
        else p.loc["Other races female"].item() / female_total * 100
    )

    proportions = pd.DataFrame(
        {
            "White": [male_white, female_white],
            "Black": [male_black, female_black],
            "Other": [male_other, female_other],
        },
        index=["Male", "Female"],
    ).round(2)

    msa_tables_1980[msa] = proportions

    print(f"\n=== {msa} ===")
    print(proportions)

# %%
merged_pop_1980 = merged_pop_1980.merge(
    total_pop[["metro13", "MSA Population"]],
    on="metro13",
    how="left",  # left join keeps all df_main rows
)
print(merged_pop_1980.head())

# %%
print(merged_pop_1980.columns)

# %% [markdown]
# ### make 1980 look like 2022 data structure

# %%
age_groups_with_total = ["Total Population"] + merged_pop_1980.columns[3:-4].to_list()

id_vars = [
    "Year of Estimate",
    "FIPS State and County Codes",
    "metro13",
    "metro_title",
]

# stack the age groups (+ Total Population) into a single column
long_df = merged_pop_1980.melt(
    id_vars=id_vars + ["Race/Sex Indicator"],
    value_vars=age_groups_with_total,
    var_name="AGEGRP",
    value_name="Population",
)

# normalize the race/sex label for gender detection
rsi_norm = long_df["Race/Sex Indicator"].astype(str).str.strip().str.lower()

# add an MSA Pop per age group as a new "race/sex" category
msa_totals = long_df.groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)[
    "Population"
].sum()
msa_totals["Race/Sex Indicator"] = "MSA Population"

# calculate gender totals
male_mask = rsi_norm.str.endswith(" male")
female_mask = rsi_norm.str.endswith(" female")

total_male = (
    long_df.loc[male_mask]
    .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
    .sum()
)
total_male["Race/Sex Indicator"] = "Total male"
total_male["Race/Sex Indicator"]
total_female = (
    long_df.loc[female_mask]
    .groupby(id_vars + ["AGEGRP"], as_index=False, observed=True)["Population"]
    .sum()
)
total_female["Race/Sex Indicator"] = "Total female"

# append the computed categories
long_augmented = pd.concat(
    [long_df, msa_totals, total_male, total_female], ignore_index=True
)

# each Race/Sex Indicator (incl. MSA Population) becomes a column
pop_1980_wide = long_augmented.pivot_table(
    index=id_vars + ["AGEGRP"],
    columns="Race/Sex Indicator",
    values="Population",
    aggfunc="sum",  # safe if duplicates exist
).reset_index()
pop_1980_wide.columns.name = None

# turn each age group into integer; 0 for "Total Population"
age_id_map = {name: i for i, name in enumerate(age_groups_with_total)}
pop_1980_wide["AGEGRP"] = pop_1980_wide["AGEGRP"].map(age_id_map).astype("Int64")

# put key aggregates first
race_cols = [c for c in pop_1980_wide.columns if c not in id_vars + ["AGEGRP"]]
preferred = [
    c for c in ["MSA Population", "Total male", "Total female"] if c in race_cols
]
others = [c for c in race_cols if c not in preferred]
race_cols = preferred + others

final_pop_1980 = (
    pop_1980_wide.sort_values(id_vars + ["AGEGRP"]).reset_index(drop=True)
)[id_vars + ["AGEGRP"] + race_cols]

# final_df
print(final_pop_1980.head(20))

# %%
# rename columns to match 2022
final_pop_1980 = final_pop_1980.rename(
    columns={
        "MSA Population": "TOT_POP",
        "Total male": "TOT_MALE",
        "Total female": "TOT_FEMALE",
        "Black female": "BAC_FEMALE",
        "Black male": "BAC_MALE",
        "Other races female": "OTHER_FEMALE",
        "Other races male": "OTHER_MALE",
        "White female": "WAC_FEMALE",
        "White male": "WAC_MALE",
        "Year of Estimate": "year",
    }
)
print(final_pop_1980)

# %% [markdown]
# ## 2022

# %% [markdown]
# ### data wrangling

# %% [markdown]
# codebook: https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2023/CBSA-EST2023-ALLDATA-CHAR.pdf

# %%
pop2 = pd.read_csv("../../data/pop_2022.csv", encoding="latin1").drop(
    columns=["MDIV", "LSAD", "SUMLEV"]
)
pop2 = pop2.query(
    "`YEAR` == 4"
)  # 1 = 4/1/2020 population estimates, 2 = 7/1/2020, 3 = 7/1/2021, 4 = 7/1/2022, 5 = 7/1/2023
pop2 = pop2.drop(columns=["YEAR"])
print(pop2)

# %%
# keep only rows relevant to bfi dataset
merged_pop_2022 = pop2.merge(
    bfi_df[["metro13", "metro_title"]],
    left_on="CBSA",
    right_on="metro13",
    how="inner",
).drop(columns=["CBSA", "NAME"])
print(merged_pop_2022)

# %%
# organize to look lik 1980 data
min_df_2022 = merged_pop_2022.query("`AGEGRP` == 0")
min_df_2022 = min_df_2022[
    [
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
]
min_df_2022["OTHER_MALE"] = merged_pop_2022[
    ["IAC_MALE", "AAC_MALE", "NAC_MALE", "H_MALE"]
].sum(axis=1)
min_df_2022["OTHER_FEMALE"] = merged_pop_2022[
    ["IAC_FEMALE", "AAC_FEMALE", "NAC_FEMALE", "H_FEMALE"]
].sum(axis=1)
print(min_df_2022)

# %%
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

# male race shares within each MSA
male_props = msa_totals[
    ["metro_title", "WAC_MALE", "BAC_MALE", "OTHER_MALE", "TOT_MALE"]
].copy()
male_props[["White", "Black", "Other"]] = male_props[
    ["WAC_MALE", "BAC_MALE", "OTHER_MALE"]
].div(male_props["TOT_MALE"], axis=0)
male_props = male_props[["metro_title", "White", "Black", "Other"]].rename_axis(
    None, axis=1
)

# female race shares within each MSA
female_props = msa_totals[
    ["metro_title", "WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE", "TOT_FEMALE"]
].copy()
female_props[["White", "Black", "Other"]] = female_props[
    ["WAC_FEMALE", "BAC_FEMALE", "OTHER_FEMALE"]
].div(female_props["TOT_FEMALE"], axis=0)
female_props = female_props[["metro_title", "White", "Black", "Other"]].rename_axis(
    None, axis=1
)


for msa in msa_totals["metro_title"]:
    male_row = male_props.loc[
        male_props["metro_title"] == msa, ["White", "Black", "Other"]
    ].squeeze()
    female_row = female_props.loc[
        female_props["metro_title"] == msa, ["White", "Black", "Other"]
    ].squeeze()

    proportions = pd.DataFrame(
        [male_row.to_numpy(), female_row.to_numpy()],
        index=["Male", "Female"],
        columns=["White", "Black", "Other"],
    ).astype(float)
    proportions = (proportions * 100).round(2)
    msa_tables_2022[msa] = proportions

    print(f"\n=== {msa} ===")
    print(proportions)

# %% [markdown]
# # Employment

# %%
ind_1980 = pd.read_csv("../../data/labor_1980.csv").drop(
    columns=["own_code", "industry_code", "qtr"]
)
ind_1980["area_fips"] = pd.to_numeric(ind_1980["area_fips"], errors="coerce")
print(ind_1980)

# %%
ind_2022 = pd.read_csv("../../data/labor_2022.csv").drop(
    columns=["own_code", "industry_code", "qtr"]
)
ind_2022["area_fips"] = pd.to_numeric(ind_2022["area_fips"], errors="coerce")
print(ind_2022)

# %%
all_ind = pd.concat([ind_1980, ind_2022])
print(all_ind)

# %%
# add msa codes to each county
msa_all_ind = all_ind.merge(
    msa_county[["ssacounty", "fipscounty", "cbsaname"]],
    left_on="area_fips",
    right_on="fipscounty",
    how="inner",
).drop(columns=["fipscounty"])
print(msa_all_ind)

# %%
# keep only rows relevant to bfi dataset
merged_all_ind = msa_all_ind.merge(
    bfi_df[["metro13", "metro_title"]],
    left_on="ssacounty",
    right_on="metro13",
    how="inner",
).drop(columns=["ssacounty", "cbsaname", "area_fips", "industry_title"])
merged_all_ind = merged_all_ind.query('`own_title` == "Total Covered"')

# %%
print(merged_all_ind.columns)

# %%
cols = [
    "metro13",
    "metro_title",
    "year",
    "annual_avg_estabs_count",
    "annual_avg_emplvl",
    "total_annual_wages",
    "annual_avg_wkly_wage",
]

agg_df = merged_all_ind.groupby(["metro13", "metro_title", "year"], as_index=False).agg(
    {
        "annual_avg_estabs_count": "sum",
        "annual_avg_emplvl": "sum",
        "total_annual_wages": "sum",
        "annual_avg_wkly_wage": "mean",
    }
)


msa_tables = {}

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

    if len(sub["year"].unique()) > 1:
        years = sorted(sub["year"].unique())
        y0, y1 = years[0], years[-1]
        table["% Change"] = ((table[y1] - table[y0]) / table[y0] * 100).round(2)

    msa_tables[msa] = table.round(2)


for msa, table in msa_tables.items():
    print(f"=== {msa} ===")
    print(table)

# %% [markdown]
# # Merge into large dataset with BFI

# %%
bfi_df1980 = bfi_df.copy()
bfi_df1980["year"] = 1980
bfi_df2022 = bfi_df.copy()
bfi_df2022["year"] = 2022
bfi_yrs = pd.concat([bfi_df1980, bfi_df2022])
print(bfi_yrs.head())
print(bfi_yrs.tail())

# %%
# merge population dataframes
tot_final_pop_1980 = final_pop_1980.query("`AGEGRP` == 0")
min_df_2022["year"] = 2022
pop_df = pd.concat([final_pop_1980, min_df_2022], ignore_index=True, axis=0).drop(
    ["FIPS State and County Codes", "AGEGRP"], axis=1
)
print(pop_df)

# %%
# make year column consistent
min_df_2022["year"] = 2022
for x in pop_df.columns:
    pop_df = pop_df.rename(columns={x: x.lower()})

# %%
new_bfi_df = bfi_yrs.merge(
    pop_df.drop(columns="metro_title"),
    on=["metro13", "year"],
    how="left",
).merge(
    merged_all_ind[
        [
            "metro13",
            "year",
            "annual_avg_estabs_count",
            "annual_avg_emplvl",
            "total_annual_wages",
            "annual_avg_wkly_wage",
        ]
    ],
    on=["metro13", "year"],
    how="left",
)
new_bfi_df = new_bfi_df.rename(
    columns={
        "race/sex indicator": "race/sex_indicator",
        "total population": "total_population",
    }
)
print(new_bfi_df)

# %%
print(new_bfi_df.columns)
