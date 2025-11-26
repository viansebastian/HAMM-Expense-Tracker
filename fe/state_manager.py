import streamlit as st
from services.api import get_budgets, get_categories, get_transactions


def load_all_user_data():
    token = st.session_state.jwt
    if "categories" not in st.session_state:
        st.session_state.categories = get_categories(token=token)

    if "budgets" not in st.session_state:
        st.session_state.budgets = get_budgets(token=token)

    if "transactions" not in st.session_state:
        st.session_state.transactions = get_transactions(token=token)

    # You can create DataFrames here if needed:
    # st.session_state.trans_df = pd.DataFrame(st.session_state.transactions)
    
    if st.session_state.get("refresh"):
        st.session_state.categories = get_categories(token=token)
        st.session_state.transactions = get_transactions(token=token)
        st.session_state.budgets = get_budgets(token=token)
        st.session_state.refresh = False

def logout():
    for key in ["jwt", "user_id", "welcome_done", "logged_in"]:
        if key in st.session_state:
            del st.session_state[key]
