import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from snowflake.snowpark import Session
from src.storage.snowflake.transformations.gold_standard.sales import GoldStandardSalesTransformation
from src.web.streamlit.features.progress_bar import sales_target

st.set_page_config(
    layout="wide"
)

st.logo("https://res.cloudinary.com/dwuzrptk6/image/upload/v1732139306/d97489eb-0834-40e3-a5b5-e93c2f0066b3_1-removebg-preview_1_z60jh6.png", size="large")

st.sidebar.page_link("./dashboards/pages/gold_standard/sets.py", label="Sets")
st.sidebar.page_link("./dashboards/pages/gold_standard/sales.py", label="Sales")
st.sidebar.page_link("./dashboards/pages/gold_standard/gold_standard.py", label="Gold Standard")
st.sidebar.page_link("./dashboards/pages/gold_standard/leaderboards.py", label="Leaderboards")

st.sidebar.divider()

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

# Set the local timezone
local_tz = pytz.timezone('America/Los_Angeles')  # Replace with your time zone

# Get the current date and time in the local timezone
now = datetime.now(local_tz)

# Sidebar for selecting month and year
st.sidebar.header("Select Month and Year")

# Month selector
month = st.sidebar.selectbox(
    "Month",
    options=list(range(1, 13)),
    format_func=lambda x: datetime(1900, x, 1).strftime('%B'),
    index=now.month - 1  # Default to current month
)

# Year selector (adjust the range as needed)
current_year = now.year
year = st.sidebar.selectbox(
    "Year",
    options=list(range(current_year - 5, current_year + 1)),  # Past 5 years + current year
    index=5  # Default to current year (assuming the list starts 5 years ago)
)

transformation = GoldStandardSalesTransformation(session)

# Process sales data based on selected month and year
df = transformation.transform(month, year)

if df.empty:
    st.warning("No sales data available for the selected month and year.")

# Create columns to display sales targets
num_columns = 3  # Adjust as needed
columns = st.columns(num_columns)

# Iterate over each row in the dataframe and display sales targets
for idx, row in df.iterrows():
    with columns[idx % num_columns]:
        sales_target(
            area=row['AREA'],
            pace=row['PACE'],
            minimum_target=row['MIN_GOAL'],
            maximum_target=row['MAX_GOAL'],  # Adjust if necessary
            actual=row['ID'],
            image=row['PROFILE_PICTURE']
        )