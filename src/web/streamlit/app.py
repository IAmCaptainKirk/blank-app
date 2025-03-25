import streamlit as st
import src.web.streamlit.dashboards.appointments as appointments
import src.web.streamlit.dashboards.gold_standard as gold_standard

def home_page():
    container = st.container()
    container.image("assets/images/logo.svg", width=75)

    container.title("Welcome!")
    container.write("Welcome to the Purelight Power dashboards app. Please select a dashboard below to view:")

    st.page_link(appointments.pages[0], label="Appointments")
    st.page_link(gold_standard.pages[0], label="Gold Standard")

pages = []

pages.append(st.Page(home_page))
pages.extend(appointments.pages)
pages.extend(gold_standard.pages)

page = st.navigation(pages)
page.run()