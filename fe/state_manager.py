import streamlit as st
from services.api import get_budgets, get_categories, get_transactions


def transform_transaction_data(transactions_list):
    """Converts API transaction list into a clean DataFrame for the UI."""
    if not transactions_list:
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])

    df = pd.DataFrame(transactions_list)

    # 1. Rename columns to match UI expectations (Date, Category, Amount)
    # The API returns lowercase keys; the frontend requires capitalized keys.
    df.rename(columns={
        'transaction_date': 'Date',
        'category_id': 'Category',  # Assuming the backend returns category NAME for display
        'amount': 'Amount',
        'type': 'Type',
        'description': 'Description'
    }, inplace=True)
    
    # 2. Ensure correct data types for plotting/calculation
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Type'] = df['Type'].str.capitalize()
    
    # Filter to only keep necessary columns, ensuring consistent order
    return df[['Date', 'Type', 'Category', 'Amount', 'Description']]

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
