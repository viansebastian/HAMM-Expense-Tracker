import streamlit as st 
import pandas as pd
import requests 
# Import API functions for fetching data
from services.api import get_transactions, group_transactions_by_type_category, predict_by_type, get_categories 

# Function to format currency (assuming Indonesian Rupiah context or similar structure)
def format_currency(value):
    # This format logic specifically handles Indonesian Rupiah dot/comma separation
    # by swapping them for display. Change this if your actual currency is USD/etc.
    return f"Rp{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def render():
    st.header("📊 Dashboard Overview")

    if "jwt" not in st.session_state:
        st.warning("You must log in first.")
        return

    # Initialize token
    token = st.session_state.jwt
    df = pd.DataFrame()
    category_map = {}
    
    # --- 1. FETCH MAIN TRANSACTION DATA ---
    
    # 1a. Fetch all transactions
    transactions_response = get_transactions(token)
    
    if transactions_response.status_code == 200:
        transactions_data = transactions_response.json()
        df = pd.DataFrame(transactions_data)
        
        # Clean data and convert types
        if not df.empty:
            df['amount'] = df['amount'].astype(float)
            df['transaction-date'] = pd.to_datetime(df['transaction-date'])
            # Rename columns for easier use
            df.rename(columns={'type': 'Type', 'amount': 'Amount', 'transaction-date': 'Date', 'category_id': 'Category_ID'}, inplace=True)
            
            # --- Fetch Category data for mapping ---
            categories_response = get_categories(token)
            if categories_response.status_code == 200:
                categories_data = categories_response.json()
                category_map = {c['id']: c['name'] for c in categories_data}
                df['Category_Name'] = df['Category_ID'].map(category_map)
            else:
                st.warning("Failed to fetch category data. Some charts might not work.")

    elif transactions_response.status_code == 404:
        st.error("Failed to fetch data: User not found or invalid token.")
        df = pd.DataFrame()
    else:
        st.error(f"Failed to fetch transactions. Status code: {transactions_response.status_code}")
        df = pd.DataFrame()


    if df.empty:
        st.info("No transactions yet. Add one in the 'Transactions' section.")
        return
    
    # --- 2. CALCULATE MAIN METRICS (Income, Expense, Balance) ---
    income = df[df['Type'] == 'income']['Amount'].sum()
    expense = df[df['Type'] == 'expense']['Amount'].sum()
    balance = income - expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income 💰", format_currency(income))
    col2.metric("Total Expenses 💸", format_currency(expense))
    col3.metric("Current Balance 💵", format_currency(balance))

    st.subheader("---")

    # --- 3. CHART: Grouping by Category and Type ---
    st.subheader("📊 Income & Expense Analysis by Category")

    group_response = group_transactions_by_type_category(token)
    
    if group_response.status_code == 200:
        grouped_data = group_response.json()
        
        # Separate Income and Expense data
        income_groups = grouped_data.get('income', [])
        expense_groups = grouped_data.get('expense', [])

        group_col1, group_col2 = st.columns(2)

        # Chart Expense by Category
        with group_col1:
            st.markdown("##### 📉 Expenses per Category")
            if expense_groups:
                df_expense = pd.DataFrame(expense_groups)
                df_expense['total_amount'] = df_expense['total_amount'].astype(float)
                
                if category_map:
                    df_expense['Category_Name'] = df_expense['category_id'].map(category_map)
                else:
                    df_expense['Category_Name'] = 'ID: ' + df_expense['category_id'].astype(str)
                    
                # Display Bar Chart
                st.bar_chart(df_expense.set_index('Category_Name')['total_amount'])
            else:
                st.info("No grouped expense data yet.")

        # Chart Income by Category
        with group_col2:
            st.markdown("##### 📈 Income per Category")
            if income_groups:
                df_income = pd.DataFrame(income_groups)
                df_income['total_amount'] = df_income['total_amount'].astype(float)
                
                if category_map:
                    df_income['Category_Name'] = df_income['category_id'].map(category_map)
                else:
                    df_income['Category_Name'] = 'ID: ' + df_income['category_id'].astype(str)

                # Display Bar Chart
                st.bar_chart(df_income.set_index('Category_Name')['total_amount'])
            else:
                st.info("No grouped income data yet.")
                
    else:
        st.warning("Failed to fetch category grouping data.")


    # --- 4. CHART: Prediction (AI Prediction) ---
    st.subheader("🔮 2-Month Transaction Prediction (AI)")

    pred_col1, pred_col2 = st.columns(2)

    # Helper function to fetch and display predictions
    def fetch_and_display_prediction(tx_type, col):
        with col:
            st.markdown(f"##### {'➕' if tx_type == 'income' else '➖'} **{tx_type.capitalize()}** Prediction")
            predict_response = predict_by_type(token, tx_type) 
            if predict_response.status_code == 200:
                pred_data = predict_response.json()
                
                # Prepare data for charting
                # Format history: [['202501', amount], ['202502', amount], ...]
                history_df = pd.DataFrame(pred_data['history'], columns=['Month_Code', 'Amount'])
                
                # Create readable month labels (e.g., '2025-01')
                history_df['Month'] = history_df['Month_Code'].astype(str).str.slice(0, 4) + '-' + history_df['Month_Code'].astype(str).str.slice(4)
                
                # Create labels for prediction months
                last_month_code = history_df['Month_Code'].iloc[-1]
                last_year = int(str(last_month_code)[:4])
                last_month = int(str(last_month_code)[4:])
                
                # Simple logic to get the next 2 month labels
                def get_next_month_label(y, m, offset):
                    m = m + offset
                    if m > 12:
                        y += 1
                        m -= 12
                    return f"{y}-{m:02d} (Predicted)"
                
                next_months_labels = [
                    get_next_month_label(last_year, last_month, 1),
                    get_next_month_label(last_year, last_month, 2)
                ]
                
                prediction_df = pd.DataFrame({
                    'Month': next_months_labels,
                    'Amount': pred_data['predicted_next_months']
                })
                
                # Combine historical and predicted data
                final_pred_df = pd.concat([history_df[['Month', 'Amount']], prediction_df])
                final_pred_df.set_index('Month', inplace=True)
                
                st.line_chart(final_pred_df['Amount'])
                st.caption(f"Next month's predictions: {format_currency(pred_data['predicted_next_months'][0])} and {format_currency(pred_data['predicted_next_months'][1])}")
            
            elif predict_response.status_code == 400:
                # Backend returns 400 if data is less than 3 months
                st.warning(f"{tx_type.capitalize()} Prediction: Insufficient data (Need > 3 months).")
            else:
                st.info(f"{tx_type.capitalize()} Prediction not available at the moment.")

    # Call function for Income and Expense
    fetch_and_display_prediction("income", pred_col1)
    fetch_and_display_prediction("expense", pred_col2)