import streamlit as st
from snowflake.snowpark import Session
from src.storage.snowflake.repositories.gold_standard.team_members import GoldStandardTeamMemberRepository
from src.web.streamlit.features.progress_bar import gold_standard

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

st.markdown("""
    <style>
    .card {
        background-color: #41434A;
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
        width: 45px;
        height: 45px;
        margin-right: 15px;
    }
    .name {
        font-size: 16px;
        font-weight: bold;
    }
    .appointments {
        font-size: 16px;
        margin-bottom: 10px;
        color: white;
    }
    .progress-bar {
        background-color: #37383C;
        border-radius: 25px;
        width: 100%;
        height: 20px;
        position: relative;
        margin-bottom: 10px;
    }
    .progress-bar-fill {
        background-color: #C34547;
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
    ._container_51w34_1 {
        display: none !important;
    }
    }
    </style>
""", unsafe_allow_html=True)

team_members = GoldStandardTeamMemberRepository(session)
gs_df = team_members.find_all()

month_options = ['This Month', 'Last Month']

with st.sidebar:
    month_selection = st.radio('Choose Month', month_options, horizontal=True, label_visibility="hidden")

# Sort the DataFrame by the selected month's data
if month_selection == 'This Month':
    gs_df = gs_df.sort_values(by='CURRENT_MONTH_SALES_AND_ASSISTS', ascending=False)
else:
    gs_df = gs_df.sort_values(by='PREVIOUS_MONTH_SALES_AND_ASSISTS', ascending=False)

# Create the layout for the cards
num_columns = 3  # Number of columns per row
columns = st.columns(num_columns)

# Iterate through the sorted DataFrame and place cards in the appropriate column
for idx, row in gs_df.reset_index(drop=True).iterrows():
    col_idx = idx % num_columns  # Determine which column to place the card
    with columns[col_idx]:
        # Determine the actual value based on the selected month
        if month_selection == 'This Month':
            actual_value = row['CURRENT_MONTH_SALES_AND_ASSISTS']
        else:
            actual_value = row['PREVIOUS_MONTH_SALES_AND_ASSISTS']

        gold_standard(
            name=row['NAME'],
            goal=row['GOAL'],
            actual=actual_value,
            profile_image=row['PICTURE_LINK']
        )