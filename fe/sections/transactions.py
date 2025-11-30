import streamlit as st
import pandas as pd
from datetime import date
from services.api import create_transaction, get_categories 
from state_manager import load_all_user_data 


def render(current_page):
    """
    Renders the unified Transactions page, including the Add Form and the View/Edit Table.
    """
    
    df = st.session_state.get('transactions_df', pd.DataFrame())
    user_id = st.session_state.get('user_id', 6)
    token = st.session_state.get('jwt', 'MOCK_TOKEN') 
    
    st.title("Transactions Management")

    st.subheader("➕ Quick Add Transaction")
    _render_add_transaction_form(user_id, token)

    st.subheader("📋 View / Edit Recent Transactions")
    _render_view_edit_data(df, user_id, token)


def _render_add_transaction_form(user_id, token):
    """Renders the form and handles the API POST request."""
    
    categories_list = st.session_state.get('categories', [])
    
    category_names = [c['name'] for c in categories_list] if categories_list else ["Food", "Salary", "Other"] # Fallback
        
    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            t_date = st.date_input("Date", value=date.today())
            t_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
            
        with col2:
            t_cat_name = st.selectbox("Category", category_names) # User selects the NAME
            t_amount = st.number_input("Amount", min_value=0.0, step=0.01)

        with col3:
            st.write("Description:")
            t_desc = st.text_input(" ", label_visibility="collapsed")
        
        submitted = st.form_submit_button("Add Transaction", type="primary")

        if submitted and t_amount > 0:

            try:
                category_id_map = {c['name']: c['id'] for c in categories_list}
                t_cat_id = category_id_map.get(t_cat_name)
                
                if t_cat_id is None:
                    st.error(f"Could not find ID for category '{t_cat_name}'. Please refresh settings.")
                    return
            except Exception as e:
                st.error(f"Category mapping error: {e}")
                return
            # ------------------------------------------

            formatted_date = t_date.strftime('%d-%m-%Y') 
            
            try:
                response = create_transaction(
                    token=token,
                    user_id=user_id, 
                    category_id=t_cat_id, # <--- PASSING INTEGER ID
                    amount=t_amount,
                    description=t_desc,
                    tx_type=t_type.lower(),
                    tx_date=formatted_date
                )
                
                response_status = response.status_code
                
                if response_status == 201:
                    st.session_state.refresh = True
                    st.success("Transaction added successfully! Refreshing data...")
                    st.rerun() 
                else:
                    st.error(f"Failed to add transaction. API returned status {response_status}. Response: {response.text}")
            
            except Exception as e:
                st.error(f"An error occurred during API call: {e}")
        elif submitted and t_amount <= 0:
            st.warning("Please enter a valid amount.")


def _render_view_edit_data(df, user_id, token):
    """Renders the editable DataFrame."""
    
    if df.empty:
        st.info("No transactions recorded yet.")
        return
    
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Type": "Type",
            "Category": "Category",
            "Amount": st.column_config.NumberColumn(format="Rp. %.0f"),
            "Description": "Description",
        }
    )
    st.caption(f"Total Transactions: {len(df)}")