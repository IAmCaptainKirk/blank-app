import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.logo("https://i.ibb.co/bbH9pgH/Purelight-Logo.webp")


st.sidebar.page_link("./dashboards/pages/appointments/targets.py", label="Targets")
st.sidebar.page_link("./dashboards/pages/appointments/web.py", label="Web Appointments")
st.sidebar.page_link("./dashboards/pages/appointments/fm.py", label="FM Appointments")

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

# Check if data has been updated
if st.session_state.get('data_updated', False):
    # Clear the cache of this page
    st.cache_data.clear()
    # Reset the data_updated flag
    st.session_state['data_updated'] = False

# Function to execute a SQL query and return a pandas DataFrame
@st.cache_data(ttl=600)
def run_query(query, data_version):
    return session.sql(query).to_pandas()

goals_query = """
    SELECT 
    b.MARKET_GROUP, 
    b.RANK AS MARKET_RANK, 
    b.NOTES, 
    a.GOAL, 
    a.MARKET, 
    a.TYPE, 
    a.RANK, 
    a.ACTIVE, 
    a.CLOSER_ID, 
    a.PROFILE_PICTURE, 
    CONCAT(SPLIT_PART(a.NAME, ' ', 1), ' ', LEFT(SPLIT_PART(a.NAME, ' ', 2), 1), '.') AS NAME,
    TIMEFRAME
FROM 
    raw.snowflake.lm_appointments a
LEFT JOIN 
    raw.snowflake.lm_markets b 
    ON a.MARKET = b.MARKET
JOIN (SELECT 'This Week' AS timeframe UNION ALL SELECT 'Last Week' AS timeframe UNION ALL SELECT 'Next Week' AS timeframe)
WHERE 
    a.ACTIVE = 'Yes' 
    AND a.TYPE IN ('🏠🏃 Hybrid', '🏠 Web To Home')
    AND (a.IS_DELETED != 'true' OR a.IS_DELETED IS NULL)
"""

appts_query = """
    SELECT owner_id closer_id, COUNT(first_scheduled_close_start_date_time_c) APPOINTMENTS, CASE
        WHEN WEEK(first_scheduled_close_start_date_time_c) = WEEK(DATEADD("day", -7, CURRENT_DATE()))
            AND YEAR(first_scheduled_close_start_date_time_c) = YEAR(DATEADD("day", -7, CURRENT_DATE())) THEN 'Last Week'
        WHEN WEEK(first_scheduled_close_start_date_time_c) = WEEK(CURRENT_DATE())
            AND YEAR(first_scheduled_close_start_date_time_c) = YEAR(CURRENT_DATE) THEN 'This Week'
        WHEN WEEK(first_scheduled_close_start_date_time_c) = WEEK(DATEADD("day", 7, CURRENT_DATE()))
            AND YEAR(first_scheduled_close_start_date_time_c) = YEAR(DATEADD("day", 7, CURRENT_DATE())) THEN 'Next Week'
    END timeframe,
    CURRENT_TIMESTAMP last_updated_at
    FROM raw.salesforce.opportunity
    WHERE sales_channel_c = 'Web To Home' 
    AND timeframe IS NOT NULL
    GROUP BY closer_id, timeframe
"""

# Ensure data_version exists
data_version = st.session_state.get('data_version', 0)

df_goals = run_query(goals_query, data_version)
df_appts = run_query(appts_query, data_version)


df = pd.merge(df_goals, df_appts, left_on=['CLOSER_ID', 'TIMEFRAME'], right_on=['CLOSER_ID', 'TIMEFRAME'], how='left')

df["TIMEFRAME"] = df["TIMEFRAME"].fillna("This Week").astype(str)
df["APPOINTMENTS"] = df["APPOINTMENTS"].fillna(0).astype(int)
df['PROFILE_PICTURE'] = df['PROFILE_PICTURE'].fillna('https://i.ibb.co/ZNK5xmN/pdycc8-1-removebg-preview.png').astype(str)

# Calculate PERCENTAGE_TO_GOAL, handling division by zero
df['PERCENTAGE_TO_GOAL'] = np.where(
    df['GOAL'] == 0, 100,  # If GOAL is 0, set percentage to 100
    np.minimum((df['APPOINTMENTS'] / df['GOAL']) * 100, 100)  # Otherwise, calculate the percentage and cap it at 100
)

st.markdown("""
    <style>
    .css-18e3th9 {
        padding-top: 0 !important;  /* Remove the space at the top */
    }
    .card {
        background-color: #1e1e1e;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        color: white;
        position: relative;
    }
    .profile-section {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .profile-pic {
        border-radius: 50%;
        width: 28px;
        height: 28px;
        margin-right: 15px;
    }
    .name {
        font-size: 16px; /* Reduced from 18px for smaller titles */
        font-weight: bold;
    }
    .appointments {
        font-size: 16px;
        margin-bottom: 10px;
        color: white;
    }
    .progress-bar {
        background-color: #333;
        border-radius: 25px;
        width: 100%;
        height: 20px;
        position: relative;
        margin-bottom: 10px;
    }
    .progress-bar-fill {
        background-color: #FF6347;
        height: 100%;
        border-radius: 25px;
    }
    .goal {
        position: absolute;
        right: 5px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 16px;
        color: white;
        font-weight: bold;
    }
    .css-1d391kg { /* New class for the market headers */
        margin-bottom: 0 !important; /* Removes extra space below headers */
    }
    </style>
""", unsafe_allow_html=True)


df['MARKET_GROUP'] = df['MARKET_GROUP'].fillna('No Group').astype(str)

# Sort the DataFrame by MARKET_RANK and RANK
df_sorted = df.sort_values(by=['MARKET_RANK', 'MARKET', 'RANK'])


# Sidebar filters with default values from query params
st.sidebar.title("Filters")

# Read query parameters
query_params = st.query_params

# Get default filter values from query params
default_selected_group = query_params.get('selected_group', ['All Groups'])
default_selected_timeframe = query_params.get('selected_timeframe', ['This Week'])[0]

# Ensure default_selected_timeframe is a valid option
valid_timeframes = ['This Week', 'Next Week', 'Last Week']
if default_selected_timeframe not in valid_timeframes:
    default_selected_timeframe = 'This Week'  # Set a fallback value

selected_group = st.sidebar.multiselect(
    'Group', 
    ['All Groups'] + sorted(df['MARKET_GROUP'].unique()),
    default=default_selected_group,
    key='group_multiselect'
)

selected_timeframe = st.sidebar.selectbox(
    'Timeframe',
    valid_timeframes,
    index=valid_timeframes.index(default_selected_timeframe)  # Safe fallback is guaranteed here
)

# Function to update query parameters
def update_query_params():
    st.query_params = {
        "selected_group": selected_group,
        "selected_timeframe": selected_timeframe
    }

# Update query parameters when filters change
update_query_params()

# Apply filters to the DataFrame
if 'All Groups' not in selected_group:
    df_sorted = df_sorted[df_sorted['MARKET_GROUP'].isin(selected_group)]

if 'TIMEFRAME' in df.columns:
    df_sorted = df_sorted[df_sorted['TIMEFRAME'] == selected_timeframe]
else:
    st.error("TIMEFRAME column not found in the dataframe.")

# Define the number of cards per row (e.g., 3, 4, 6)
cards_per_row = 3

market_cols = st.columns(2)

# Group by MARKET and loop over each group
for idx, (market, group_df) in enumerate(df_sorted.groupby('MARKET')):
    # Alternate between the two columns for each market
    col = market_cols[idx % 2]
    
    with col:
        # Add a header for each market group
        if 'NOTES' in group_df.columns and not group_df['NOTES'].isna().all():
            notes = group_df['NOTES'].iloc[0]  # Get the first non-null value
        else:
            notes = ''
        st.header(market, help=notes)

        # Break the group into chunks (rows of cards)
        for i in range(0, len(group_df), cards_per_row):
            row_df = group_df.iloc[i:i + cards_per_row]  # Get a chunk of cards (one row)

            # Create columns for this row (inside each market column)
            cols = st.columns(cards_per_row)

            # Loop through each card in the row and assign it to a column
            for col, (_, row) in zip(cols, row_df.iterrows()):
                percentage_to_goal = row['PERCENTAGE_TO_GOAL']
                goal_value = row['GOAL']
                appointments_value = row['APPOINTMENTS']
                 # Choose progress bar color based on the percentage
                
                progress_color = "#FF6347" if percentage_to_goal < 100 else "#47C547"
                
                with col:
                    st.markdown(f"""
                        <div class="card">
                            <div class="profile-section">
                                <img src="{row['PROFILE_PICTURE']}" class="profile-pic" alt="Profile Picture">
                                <div class="name">{row['NAME']}</div>
                            </div>
                            <div class="appointments">{appointments_value}</div>
                            <div class="progress-bar">
                                <div class="progress-bar-fill" style="width: {percentage_to_goal}%;background-color: {progress_color};"></div>
                                <div class="goal">{goal_value}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)