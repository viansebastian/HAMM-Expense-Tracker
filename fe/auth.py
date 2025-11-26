import streamlit as st
from services.api import login, register


def login_page():
    st.title("🔐 Login")

    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            r = login(email, pw)

            if r.status_code == 200:
                data = r.json()
                st.session_state.jwt = data["access_token"]
                st.session_state.user_id = data["user_id"]
            else:
                st.error("Invalid credentials")
        except Exception as e:
            st.error(f"Exception occurred: {e}")


def run():
    st.title("Register")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")

    if st.button("Register"):
        try:
            r = register(email, password, first_name, last_name)

            if r.status_code == 200:
                st.success("Registration successful. Please go to Login page.")
            else:
                st.error("Server error")
        except Exception as e:
            st.error(f"Exception occurred: {e}")
