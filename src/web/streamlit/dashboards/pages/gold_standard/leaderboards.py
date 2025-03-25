import streamlit as st
import datetime
from snowflake.snowpark import Session

st.set_page_config(
    layout="wide"
)

st.logo("https://res.cloudinary.com/dwuzrptk6/image/upload/v1732139306/d97489eb-0834-40e3-a5b5-e93c2f0066b3_1-removebg-preview_1_z60jh6.png", size="large")

st.sidebar.page_link("./dashboards/pages/gold_standard/sets.py", label="Sets")
st.sidebar.page_link("./dashboards/pages/gold_standard/sales.py", label="Sales")
st.sidebar.page_link("./dashboards/pages/gold_standard/gold_standard.py", label="Gold Standard")
st.sidebar.page_link("./dashboards/pages/gold_standard/leaderboards.py", label="Leaderboards")

def create_snowflake_session():
    connection_parameters = {
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "role": st.secrets["snowflake"]["role"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": st.secrets["snowflake"]["database"],
        "schema": st.secrets["snowflake"]["schema"],
    }
    return Session.builder.configs(connection_parameters).create()

session = None

try:
    session = get_active_session()
except:
    session = create_snowflake_session()

@st.cache_data(ttl=600)
def get_ec_table():
    query = """
        SELECT date "Date", closer "Closer", closer_picture_link "Closer Picture Link", area "Area", area_picture_link "Area Picture Link",COUNT(DISTINCT CASE WHEN metric = 'Sales' THEN id END) "Sales", COUNT(DISTINCT CASE WHEN metric = 'Sits' THEN id END) "Sits", COUNT(DISTINCT CASE WHEN metric = 'Opportunities' THEN id END) "Opps"
FROM analytics.team_reporting.dtbl_sales_leaderboard
GROUP BY ALL
    """
    return session.sql(query).to_pandas()

@st.cache_data(ttl=600)
def get_fm_table():
    query = """
        SELECT date "Date", lead_generator "FM", area "Area", fm_picture_link "FM Picture Link", area_picture_link "Area Picture Link", COUNT(DISTINCT CASE WHEN metric = 'Sales' THEN id END) "Assists", COUNT(DISTINCT CASE WHEN metric = 'Sits' THEN id END) "Sits", COUNT(DISTINCT CASE WHEN metric = 'Sets' THEN id END) "Sets"
FROM analytics.team_reporting.dtbl_sales_leaderboard
WHERE lead_generator IS NOT NULL
GROUP BY ALL
ORDER BY "Assists"
    """
    return session.sql(query).to_pandas()

@st.cache_data(ttl=600)
def get_contract_value_table():
    query = """
        SELECT
            id,
            sale_date "Sale Date",
            closer "Closer",
            IFNULL(closer_picture_link, 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730865202/Group_1127_zhbvez.png') "Closer Picture Link",
            fm_picture_link "FM Picture Link",
            lead_generator "Field Marketer",
            tbl_master_opportunities.area "Area",
            area_links.picture_link "Area Picture Link",
            COUNT(DISTINCT CASE WHEN project_sub_category = 'Solar' THEN id END) "Solar",
            COUNT(DISTINCT CASE WHEN project_sub_category = 'Battery' THEN id END) "Batteries",
            COUNT(DISTINCT CASE WHEN project_sub_category = 'Roof' OR project_sub_category LIKE 'Reroof%' THEN id END) "Roofs",
            COUNT(DISTINCT CASE WHEN project_sub_category LIKE 'Solar +%' THEN id END) "Bundled",
            grand_total - lender_fee_total "CV"
        FROM analytics.reporting.tbl_master_opportunities
        LEFT JOIN raw.snowflake.area_links ON tbl_master_opportunities.area = area_links.area
        GROUP BY ALL """
    return session.sql(query).to_pandas()

###############################################################################
# Pull data from queries
###############################################################################
# 1) Energy Consultant data
df = get_ec_table()

# 2) Field Marketer data
fm_df = get_fm_table()

# 3) Contract Value data
#    NOTE: We expect df_cv to have:
#      - "Sale Date" as the date column
#      - "Area"
#      - "Closer" or "Field Marketer" (depending on role)
#      - "Area Picture Link" if you want to show an image for Area
df_cv = get_contract_value_table()

###############################################################################
# Get unique areas
###############################################################################
unique_areas = sorted(df["Area"].unique())

###############################################################################
# Calculate default date range (first of current month - last day of current month)
###############################################################################
today = datetime.date.today()
if today.month == 12:
    next_month = datetime.date(today.year + 1, 1, 1)
else:
    next_month = datetime.date(today.year, today.month + 1, 1)
end_of_month = next_month - datetime.timedelta(days=1)
end_of_month_day = end_of_month.day

###############################################################################
# Sidebar-like controls
###############################################################################
cols1, cols2, cols3, cols4 = st.columns([1, 1, 1, 1])

with cols1:
    date_range = st.date_input(
        "Date",
        (
            datetime.date(today.year, today.month, 1),
            datetime.date(today.year, today.month, end_of_month_day),
        )
    )
    start_date, end_date = date_range

with cols2:
    area = st.multiselect("Area", unique_areas)

with cols3:
    dimension = st.selectbox("Dimension", ("Rep", "Area"))

with cols4:
    role = st.selectbox("Role", ("Energy Consultant", "Field Marketer"))

###############################################################################
# 1) Filter & group ENERGY CONSULTANT data (df)
###############################################################################
df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

if area:
    df_filtered = df_filtered[df_filtered["Area"].isin(area)]

# Group by dimension
if dimension == "Rep":
    ec_grouped_df = (
        df_filtered
        .groupby(["Closer", "Closer Picture Link"], as_index=False)
        [["Sales", "Sits", "Opps"]]
        .sum()
        .sort_values("Sales", ascending=False)
    )
    ec_picture_col = "Closer Picture Link"
    ec_name_col = "Closer"
else:  # dimension == "Area"
    ec_grouped_df = (
        df_filtered
        .groupby(["Area", "Area Picture Link"], as_index=False)
        [["Sales", "Sits", "Opps"]]
        .sum()
        .sort_values("Sales", ascending=False)
    )
    ec_picture_col = "Area Picture Link"
    ec_name_col = "Area"

###############################################################################
# 2) Filter & group FIELD MARKETER data (fm_df)
###############################################################################
fm_df_filtered = fm_df[(fm_df["Date"] >= start_date) & (fm_df["Date"] <= end_date)]

if area:
    fm_df_filtered = fm_df_filtered[fm_df_filtered["Area"].isin(area)]

if dimension == "Rep":
    fm_grouped_df = (
        fm_df_filtered
        .groupby(["FM", "FM Picture Link"], as_index=False)
        [["Assists", "Sits", "Sets"]]
        .sum()
        .sort_values("Assists", ascending=False)
    )
    fm_picture_col = "FM Picture Link"
    fm_name_col = "FM"
else:  # dimension == "Area"
    fm_grouped_df = (
        fm_df_filtered
        .groupby(["Area", "Area Picture Link"], as_index=False)
        [["Assists", "Sits", "Sets"]]
        .sum()
        .sort_values("Assists", ascending=False)
    )
    fm_picture_col = "Area Picture Link"
    fm_name_col = "Area"

###############################################################################
# 3) Filter & group CONTRACT VALUE data (df_cv)
###############################################################################
# 3a) Filter by date range using "Sale Date"
df_cv_filtered = df_cv[
    (df_cv["Sale Date"] >= start_date) & (df_cv["Sale Date"] <= end_date)
]

# 3b) Filter by area if selected
if area:
    df_cv_filtered = df_cv_filtered[df_cv_filtered["Area"].isin(area)]

# 3c) Decide how to group the CV data based on dimension and role
if dimension == "Rep":
    # If the user picks 'Energy Consultant', group by "Closer"
    # If the user picks 'Field Marketer', group by "Field Marketer"
    if role == "Energy Consultant":
        cv_grouped_df = (
            df_cv_filtered
            .groupby(["Closer", "Closer Picture Link"], as_index=False)
            [["CV", "Solar", "Batteries", "Roofs", "Bundled"]]
            .sum()
            .sort_values("CV", ascending=False)
        )
        cv_picture_col = "Closer Picture Link"
        cv_name_col = "Closer"
    else:  # role == "Field Marketer"
        cv_grouped_df = (
            df_cv_filtered
            .groupby(["Field Marketer", "FM Picture Link"], as_index=False)
            [["CV", "Solar", "Batteries", "Roofs", "Bundled"]]
            .sum()
            .sort_values("CV", ascending=False)
        )
        cv_picture_col = "FM Picture Link"
        cv_name_col = "Field Marketer"

else:  # dimension == "Area"
    # If your df_cv has "Area Picture Link", group by both "Area" and "Area Picture Link".
    cv_grouped_df = (
        df_cv_filtered
        .groupby(["Area", "Area Picture Link"], as_index=False)
        [["CV", "Solar", "Batteries", "Roofs", "Bundled"]]
        .sum()
        .sort_values("CV", ascending=False)
    )
    cv_picture_col = "Area Picture Link"
    cv_name_col = "Area"

# Round CV if desired
cv_grouped_df["CV"] = cv_grouped_df["CV"].round(0)

cv_grouped_df['CV'] = cv_grouped_df['CV'].apply(lambda x: f"${x:,.0f}")

###############################################################################
# Create two tabs: "Activity" (driven by 'role') and "Contract Value"
###############################################################################
tab1, tab2 = st.tabs(["Activity", "Contract Value"])

###############################################################################
# TAB 1 (Activity)
###############################################################################
with tab1:
    # If "Energy Consultant" was selected
    if role == "Energy Consultant":
        st.data_editor(
            ec_grouped_df,
            column_config={ec_picture_col: st.column_config.ImageColumn("")}
            if ec_picture_col in ec_grouped_df.columns
            else None,
            column_order=[
                col
                for col in (
                    ec_picture_col,
                    ec_name_col,
                    "Sales",
                    "Sits",
                    "Opps"
                )
                if col in ec_grouped_df.columns
            ],
            hide_index=True,
            height=1000,
            disabled=True,
            use_container_width=True,
        )
    # If "Field Marketer" was selected
    else:
        st.data_editor(
            fm_grouped_df,
            column_config={fm_picture_col: st.column_config.ImageColumn("")}
            if fm_picture_col in fm_grouped_df.columns
            else None,
            column_order=[
                col
                for col in (
                    fm_picture_col,
                    fm_name_col,
                    "Assists",
                    "Sits",
                    "Sets"
                )
                if col in fm_grouped_df.columns
            ],
            hide_index=True,
            height=1000,
            disabled=True,
            use_container_width=True,
        )

###############################################################################
# TAB 2 (Contract Value)
###############################################################################
with tab2:
    # If we have a valid picture column (e.g., Closer Picture Link, FM Picture Link, or Area Picture Link)
    if cv_picture_col and cv_picture_col in cv_grouped_df.columns:
        st.data_editor(
            cv_grouped_df,
            column_config={cv_picture_col: st.column_config.ImageColumn("")},
            column_order=[
                cv_picture_col,
                cv_name_col,
                "CV",
                "Solar",
                "Batteries",
                "Roofs",
                "Bundled",
            ],
            hide_index=True,
            disabled=True,
            use_container_width=True,
            height=1000,
        )
    else:
        # No valid picture column found, so skip that
        st.data_editor(
            cv_grouped_df,
            column_order=[
                cv_name_col,
                "CV",
                "Solar",
                "Batteries",
                "Roofs",
                "Bundled",
            ],
            hide_index=True,
            disabled=True,
            use_container_width=True,
            height=1000,
        )