import streamlit as st
import pandas as pd
from services.api import get_budgets, get_categories, get_transactions


def transform_transaction_data(transactions_list):
    if not transactions_list:
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])

    df = pd.DataFrame(transactions_list)

    if 'transaction-date' in df.columns:
        df.rename(columns={'transaction-date': 'Date'}, inplace=True)
    elif 'transaction_date' in df.columns:
        df.rename(columns={'transaction_date': 'Date'}, inplace=True)
        
    df.rename(columns={
        'category_id': 'Category', 
        'amount': 'Amount',
        'type': 'Type',
        'description': 'Description'
    }, inplace=True)
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    if 'Amount' in df.columns:
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    if 'Type' in df.columns:
        df['Type'] = df['Type'].astype(str).str.capitalize()
    
    expected_cols = ['Date', 'Type', 'Category', 'Amount', 'Description']
    safe_cols = [c for c in expected_cols if c in df.columns]
    
    return df[safe_cols]

def load_all_user_data():
    token = st.session_state.jwt
    if "categories" not in st.session_state:
        # UPDATE: Handle the Response object
        cat_resp = get_categories(token=token)
        if cat_resp and cat_resp.status_code == 200:
            st.session_state.categories = cat_resp.json()
        else:
            st.session_state.categories = []

    if "budgets" not in st.session_state:
        st.session_state.budgets = get_budgets(token=token)

    if "transactions" not in st.session_state:
        st.session_state.transactions = get_transactions(token=token)

    # You can create DataFrames here if needed:
    # st.session_state.trans_df = pd.DataFrame(st.session_state.transactions)
    
    if st.session_state.get("refresh"):
        #st.session_state.categories = get_categories(token=token)
        cat_resp = get_categories(token=token)
        if cat_resp and cat_resp.status_code == 200:
            st.session_state.categories = cat_resp.json()
        else:
            st.session_state.categories = []
       # st.session_state.transactions = get_transactions(token=token)
        st.session_state.budgets = get_budgets(token=token)
        
        resp = get_transactions(token=token)
        st.session_state.transactions = resp.json() if resp.status_code == 200 else []
        st.session_state.transactions_df = transform_transaction_data(st.session_state.transactions)
        
        st.session_state.refresh = False

def logout():
    for key in ["jwt", "user_id", "welcome_done", "logged_in"]:
        if key in st.session_state:
            del st.session_state[key]
