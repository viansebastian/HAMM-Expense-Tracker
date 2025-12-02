import streamlit as st
import pandas as pd
from datetime import datetime, date
from services.api import create_transaction, create_category, delete_category, delete_transaction

# ga pake state manager biar ga error lg LOL

def render(current_page):
    """
    Renders the unified Transactions page with 3 Tabs:
    1. Add
    2. View/Delete (with Monthly Stats)
    3. Manage Categories
    """
    st.title("💸 Transaction Hub")

    # Access data from session state
    # 'transactions_df' is the clean DataFrame from state_manager
    df = st.session_state.get('transactions_df', pd.DataFrame())
    categories = st.session_state.get('categories', [])
    user_id = st.session_state.get('user_id')
    print(user_id)
    token = st.session_state.get('jwt')

    tab_add, tab_view, tab_cat = st.tabs(["➕ Add Transaction", "👁️ View & Manage", "🏷️ Categories"])

    with tab_add:
        st.header("New Entry")
        st.caption("Record your income or expenses here.")
        _render_add_transaction_form(user_id, token, categories)

    with tab_view:
        st.header("Recorded Transactions")

        if df.empty:
            st.info("No transactions found yet. Go to the 'Add' tab to start!")
        else:
            if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                df['Date'] = pd.to_datetime(df['Date'])

            now = datetime.now()
            mask = (df['Date'].dt.month == now.month) & (df['Date'].dt.year == now.year)
            month_df = df[mask]

            st.subheader(f"Overview for {now.strftime('%B %Y')}")
            
            if not month_df.empty:
                # Calculate sums
                m_inc = month_df[month_df['Type'] == 'Income']['Amount'].sum()
                m_exp = month_df[month_df['Type'] == 'Expense']['Amount'].sum()
                m_bal = m_inc - m_exp

                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Income (This Month)", f"Rp {m_inc:,.0f}", delta="Income")
                col_m2.metric("Expense (This Month)", f"Rp {m_exp:,.0f}", delta="-Expense", delta_color="normal")
                col_m3.metric("Net Balance", f"Rp {m_bal:,.0f}")
            else:
                st.info(f"No transactions recorded for {now.strftime('%B')}.")

            st.divider()

            st.subheader("📋 All Transactions")
            
            df_display = df.sort_values(by="Date", ascending=False).copy()
            
            if categories and 'Category' in df_display.columns:
                id_map = {c['id']: c['name'] for c in categories}
                if pd.api.types.is_numeric_dtype(df_display['Category']):
                    df_display['Category'] = df_display['Category'].map(id_map).fillna("Unknown")

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="DD-MM-YYYY"),
                    "Amount": st.column_config.NumberColumn("Amount", format="Rp %.0f"),
                    "Type": st.column_config.TextColumn("Type"),
                    "Category": st.column_config.TextColumn("Category"),
                    "Description": "Desc"
                }
            )

            st.divider()
            with st.expander("🗑️ Delete a Transaction", expanded=False):
                st.warning("Action is permanent.")
                
                # We need raw transactions to get the real 'id' for the API
                raw_tx = st.session_state.get('transactions', [])
                if raw_tx:
                    # sort by date desc
                    raw_sorted = sorted(raw_tx, key=lambda x: x.get('transaction_date', ''), reverse=True)
                    # Limit to last 30 for performance in dropdown
                    raw_sorted = raw_sorted[:30]

                    def tx_format(x):
                        return f"{x.get('transaction_date')} | Rp {x.get('amount')} | {x.get('description')}"

                    tx_to_del = st.selectbox("Select Transaction to Delete", raw_sorted, format_func=tx_format)

                    if st.button("Confirm Delete", type="primary"):
                        if tx_to_del:
                            res = delete_transaction(tx_to_del['id'], token)
                            if res.status_code == 200:
                                st.success("Deleted successfully!")
                                st.session_state.refresh = True
                                st.rerun()
                            else:
                                st.error("Failed to delete.")


    with tab_cat:
        st.header("Category Manager")
        
        col_c1, col_c2 = st.columns([1, 2])
        
        # LEFT: Create
        with col_c1:
            st.subheader("Create New")
            with st.form("create_cat"):
                new_c_name = st.text_input("Name", placeholder="e.g. Coffee")
                new_c_type = st.radio("Type", ["Income", "Expense"])
                if st.form_submit_button("Add Category", type="primary"):
                    if new_c_name:
                        res = create_category(token, new_c_name, new_c_type.lower(), user_id)
                        if res.status_code == 201:
                            st.toast(f"Added {new_c_name}!", icon="✅")
                            st.session_state.refresh = True
                            st.rerun()
                        else:
                            st.error(f"Error: {res.text}")

        with col_c2:
            st.subheader("Existing Categories")
            if categories:
                cat_df = pd.DataFrame(categories)
                st.dataframe(
                    cat_df[['name', 'type']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={"name": "Name", "type": "Type"}
                )
                
                st.write("---")
                c_del_name = st.selectbox("Select Category to Delete", [c['name'] for c in categories])
                if st.button("Delete Category"):
                    c_id = next((c['id'] for c in categories if c['name'] == c_del_name), None)
                    if c_id:
                        res = delete_category(token, c_id)
                        if res.status_code == 200:
                            st.success(f"Deleted {c_del_name}")
                            st.session_state.refresh = True
                            st.rerun()
                        else:
                            st.error("Cannot delete (maybe used in transactions?)")

def _render_add_transaction_form(user_id, token, categories_list):
    """Renders the Add Transaction form."""
    
    category_names = [c['name'] for c in categories_list] if categories_list else ["Food", "Salary", "Other"]
        
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            t_date = st.date_input("Date", value=date.today())
            t_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
            t_amount = st.number_input("Amount (Rp)", min_value=0, step=1000)

        with col2:
            t_cat_name = st.selectbox("Category", category_names) 
            t_desc = st.text_input("Description", placeholder="e.g. Lunch at MKJ")
        
        submitted = st.form_submit_button("Save Transaction", use_container_width=True, type="primary")

        if submitted:
            if t_amount <= 0:
                st.warning("Please enter a valid amount.")
                return

            # Find the ID for the selected name
            try:
                category_id_map = {c['name']: c['id'] for c in categories_list}
                t_cat_id = category_id_map.get(t_cat_name)
                
                if t_cat_id is None:
                    st.error("Invalid Category. Please refresh.")
                    return
            except Exception as e:
                st.error(f"Error mapping category: {e}")
                return

            # Call API
            formatted_date = t_date.strftime('%d-%m-%Y') 
            try:
                response = create_transaction(
                    token=token,
                    user_id=user_id, 
                    category_id=t_cat_id,
                    amount=t_amount,
                    description=t_desc,
                    tx_type=t_type.lower(), # 'Income' -> 'income'
                    tx_date=formatted_date
                )
                
                if response.status_code == 201:
                    # Trigger a reload in main.py via session state
                    st.session_state.refresh = True
                    st.toast("Transaction Added!", icon="✅")
                    st.rerun() 
                else:
                    st.error(f"API Error: {response.status_code}")
            except Exception as e:
                st.error(f"Connection Error: {e}")