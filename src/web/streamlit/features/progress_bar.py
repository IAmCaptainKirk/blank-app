import streamlit as st
from datetime import datetime
from calendar import monthrange

def create_card(area, goal, actual, profile_image, name):
    # Calculate the percentage to goal, handling division by zero
    percentage_to_goal = min((actual / goal) * 100 if goal != 0 else 100, 100)
    # Set the progress bar color based on the percentage
    progress_color = "#C34547" if percentage_to_goal < 100 else "#32A077"

    st.markdown(f"""
        <div class="card">
            <div class="profile-section">
                <img src="{profile_image}" class="profile-pic" alt="Profile Picture">
                <div class="name">{name}</div>
            </div>
            <div class="appointments">{actual}</div>
            <div class="progress-bar">
                <div class="progress-bar-fill" style="width: {percentage_to_goal}%; background-color: {progress_color};"></div>
                <div class="goal">{goal}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def sales_target(actual, pace, minimum_target, maximum_target, image, area):
    # Calculate percentages
    today = datetime.today()
    total_days_in_month = monthrange(today.year, today.month)[1]
    day_of_month = today.day

    percent_through_month = (day_of_month / total_days_in_month) * 100
    percent_to_minimum = (actual / minimum_target) * 100 if minimum_target > 0 else 100
    percent_to_maximum = (actual / maximum_target) * 100 if maximum_target > 0 else 100

    # Determine colors and arrows based on comparison with % through month
    if percent_to_minimum >= percent_through_month:
        min_color = "#2C966C"  # green
        min_arrow = "🔼"
        progress_bar_color = "#2C966C"  # green
    else:
        min_color = "#BB3C3E"  # red
        min_arrow = "🔻"
        progress_bar_color = "#BB3C3E"  # red

    if percent_to_maximum >= percent_through_month:
        max_color = "#2C966C"  # green
        max_arrow = "🔼"
    else:
        max_color = "#BB3C3E"  # red
        max_arrow = "🔻"

    # Progress bar calculations
    progress_percentage = (actual / maximum_target) * 100 if maximum_target > 0 else 0
    progress_percentage = min(progress_percentage, 100)  # Cap at 100%

    # Position of the vertical line (minimum target marker)
    vertical_line_position = (minimum_target / maximum_target) * 100 if maximum_target > 0 else 0
    vertical_line_position = min(vertical_line_position, 100)


    # Generate the HTML code
    html_code = f"""
    <div style="background-color: #41434A; padding: 20px; width: 100%;border-radius: 20px; box-sizing: border-box; color: white; font-family: Arial, Helvetica, sans-serif; position: relative;">
        <!-- Include custom styles for the tooltip -->
        <style>
            .tooltip {{
                position: relative;
                display: inline-block;
                cursor: pointer;
                margin-left: 5px;
            }}
            .tooltip .tooltiptext {{
                visibility: hidden;
                width: 220px;
                background-color: #484A4F;
                color: #fff;
                text-align: left;
                border-radius: 6px;
                padding: 10px;
                position: absolute;
                z-index: 1000;
                top: 100%; /* Position the tooltip below the icon */
                right: 0%;
                margin-top: 10px;
                opacity: 0;
                transition: opacity 0.3s;
            }}
            .tooltip:hover .tooltiptext {{
                visibility: visible;
                opacity: 1;
            }}
        </style>
        <!-- Header starts here -->
        <div style="width: 95%; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; position: relative;">
            <div style="display: flex; align-items: center;">
                <img src="{image}" style="width: 40px; height: 40px; margin-right: 10px;">
                <span style="font-weight: bold; font-size: 18px;">{area}</span>
            </div>
            <!-- Tooltip with info icon on the right -->
            <div class="tooltip" style="color: #6E7076;">
                <span style="font-size: 14px; cursor: pointer;">&#9432;</span> <!-- Unicode for info symbol -->
                <div class="tooltiptext" style="font-size: 14px;">
                    <p>% through month: {percent_through_month:.0f}%</p>
                    <p>% to minimum: <span style="color: {min_color};">{percent_to_minimum:.0f}% {min_arrow}</span></p>
                    <p>% to stretch: <span style="color: {max_color};">{percent_to_maximum:.0f}% {max_arrow}</span></p>
                </div>
            </div>
        </div>
        <!-- "{actual} on pace to {pace}" line -->
        <div style="width: 95%; text-align: left; margin-bottom: 8px; font-size: 18px; font-weight: bold;">
            {actual}<span style="font-size: 14px; font-weight: normal; color: #6E7076;"> on pace to {pace}</span>
        </div>
        <!-- Progress bar and numbers container -->
        <div style="width: 95%; position: relative;">

            <!-- Progress bar container -->
            <div style="width: 100%; background: #333; border-radius: 20px; height: 20px; overflow: hidden; position: relative;">
                <!-- Progress section -->
                <div style="background: {progress_bar_color}; width: {progress_percentage}%; height: 100%;"></div>
                <!-- Vertical line at the minimum target mark -->
                <div style="position: absolute; left: {vertical_line_position}%; top: 0; height: 100%; width: 2px; background-color: #2C966C;"></div>
            </div>

            <!-- Numbers below the chart -->
            <div style="position: relative; width: 100%; height: 20px; margin-top: 8px; font-weight: bold; font-size: 14px;">
                <!-- Number at minimum target -->
                <div style="position: absolute; left: {vertical_line_position}%; transform: translateX(-50%); color: #FFFFFF;">{minimum_target}</div>
                <!-- Number at maximum target -->
                <div style="position: absolute; right: 0; color: #FFFFFF;">{maximum_target}</div>
            </div>

        </div>
    </div>
    """

    st.html(html_code)

def gold_standard(goal, actual, profile_image, name):
    # Calculate the percentage to goal, handling division by zero
    percentage_to_goal = min((actual / goal) * 100 if goal != 0 else 100, 100)
    # Set the progress bar color based on the percentage
    progress_color = "#C34547" if percentage_to_goal < 100 else "#E1AB3D"
    
    # If it's over (or equal to) the goal, add the emoji and a drop shadow
    if actual >= goal:
        name = f"{name} ⭐"
        # Instead of setting a text-shadow on the name, we apply a box-shadow to the card.

    st.markdown(f"""
    <div class="card">
        <div class="profile-section">
            <img src="{profile_image}" class="profile-pic" alt="Profile Picture">
            <div class="name">{name}</div>
        </div>
        <div class="appointments">{actual}</div>
        <div class="progress-bar">
            <div class="progress-bar-fill" style="width: {percentage_to_goal}%; background-color: {progress_color};"></div>
            <div class="goal">{goal}</div>
        </div>
    </div>
""", unsafe_allow_html=True)