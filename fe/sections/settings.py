import streamlit as st 
from state_manager import logout


def render(): 
    st.header("⚙️ Settings")

    if st.button("Logout"):
        logout()
        st.rerun()
    # if page == "Settings":
    #     st.header("⚙️ Settings")
    #     theme = st.radio("Select Theme", ["Light", "Dark"], horizontal=True)
    #     currency = st.selectbox("Preferred Currency", ["IDR", "USD", "KRW"])
    #     st.success(f"Settings saved: Theme - {theme}, Currency - {currency}")
