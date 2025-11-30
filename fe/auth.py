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
                st.session_state.logged_in = True
                st.success("Logged in!")
                st.rerun()

            else:
                st.error(f"Login failed ({r.status_code})")
                st.code(r.text)   # full backend error message

        except Exception as e:
            st.error("⚠️ Something went wrong.")
            st.exception(e)


def register_user():
    # Use a unique container to ensure key uniqueness across the application
    with st.container():
        st.title("Register")

        # FIX: Added unique 'key' arguments to all text_input elements
        email = st.text_input("Email", key="reg_email_input")
        password = st.text_input("Password", type="password", key="reg_password_input")
        first_name = st.text_input("First Name", key="reg_first_name_input")
        last_name = st.text_input("Last Name", key="reg_last_name_input")

        # Assuming 'register' should call an API, not itself recursively
        # Renamed variable 'r' to 'response' for clarity

        if st.button("Register", key="reg_button"):
            try:
                # Assuming the actual API function is imported as register_api or similar
                # Using a placeholder function name 'register_user' for this example
                response = register(email, password, first_name, last_name)
                
                # Placeholder logic: Replace with your actual API call
                st.success("Registration successful. Please go to Login page.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Exception occurred: {e}")
