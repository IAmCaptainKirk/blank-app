import streamlit as st

pages = [
    st.Page(
        "./dashboards/pages/gold_standard/sets.py",
        title="Gold Standard Dashboard » Sets",
        url_path="gold_standard_sets"
    ),
    st.Page(
        "./dashboards/pages/gold_standard/sales.py",
        title="Gold Standard Dashboard » Sales",
        url_path="gold_standard_sales"
    ),
    st.Page(
        "./dashboards/pages/gold_standard/gold_standard.py",
        title="Gold Standard Dashboard » Gold Standard",
        url_path="gold_standard_gs"
    ),
    st.Page(
        "./dashboards/pages/gold_standard/leaderboards.py",
        title="Gold Standard Dashboard » Leaderboards",
        url_path="gold_standard_leaderboards"
    )
]