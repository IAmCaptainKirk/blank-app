import streamlit as st

pages = [
    st.Page(
        "./dashboards/pages/appointments/targets.py",
        title="Appointment Dashboard » Closer Targets",
        url_path="appointments"
    ),
    st.Page(
        "./dashboards/pages/appointments/web.py",
        title="Appointment Dashboard » Web Appointments",
        url_path="appointments_web"
    ),
    st.Page(
        "./dashboards/pages/appointments/fm.py",
        title="Appointment Dashboard » FM Appointments",
        url_path="appointments_fm"
    )
]