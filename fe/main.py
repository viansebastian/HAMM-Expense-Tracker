import streamlit as st
from auth import login_page
from state_manager import load_all_user_data
from sections import dashboard, analytics, transactions, budget, settings    # your sidebar + pages

st.set_page_config(page_title="HAMM", layout="wide")

# If not logged in -> login screen
if "jwt" not in st.session_state:
    login_page()
    st.stop()
    

# Logged in but not past welcome page → show Hello World
if "welcome_done" not in st.session_state:
    st.title("🎉 Hello, world!")
    st.write("You have successfully logged in.")

    if st.button("Continue to App"):
        st.session_state.welcome_done = True

    st.stop()

# Load user data once after login
load_all_user_data()

section = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Transactions", "Analytics", "Budget", "Settings"]
)

# Render UI
if section == "Dashboard":
    dashboard.render()

elif section == "Transactions":
    transactions.render()

elif section == "Analytics":
    analytics.render()

elif section == "Budget":
    budget.render()

elif section == "Settings":
    settings.render()