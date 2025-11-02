import streamlit as st 
import requests 
import pandas as pd 


API_BASE_URL = 'http://127.0.0.1:5000'

st.set_page_config(page_title='Finance Dashboard', layout='wide')

st.title('HAMM')
st.markdown('Displaying the first 5 records from each table')

# --- Helper function ---
def get_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return []

# --- Layout ---
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# USERS
with col1:
    st.subheader("👤 Users")
    users = get_data("users")
    if users:
        st.dataframe(pd.DataFrame(users).head(5))
    else:
        st.warning("No user data found.")

# CATEGORIES
with col2:
    st.subheader("🏷️ Categories")
    categories = get_data("categories")
    if categories:
        st.dataframe(pd.DataFrame(categories).head(5))
    else:
        st.warning("No category data found.")

# TRANSACTIONS
with col3:
    st.subheader("💸 Transactions")
    transactions = get_data("transactions")
    if transactions:
        st.dataframe(pd.DataFrame(transactions).head(5))
    else:
        st.warning("No transaction data found.")

# BUDGETS
with col4:
    st.subheader("📊 Budgets")
    budgets = get_data("budgets")
    if budgets:
        st.dataframe(pd.DataFrame(budgets).head(5))
    else:
        st.warning("No budget data found.")