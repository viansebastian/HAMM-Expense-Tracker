import streamlit as st 


def render(): 
    if page == "Settings":
        st.header("⚙️ Settings")
        theme = st.radio("Select Theme", ["Light", "Dark"], horizontal=True)
        currency = st.selectbox("Preferred Currency", ["IDR", "USD", "KRW"])
        st.success(f"Settings saved: Theme - {theme}, Currency - {currency}")
