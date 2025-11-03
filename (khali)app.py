import streamlit as st
import pandas as pd
from datetime import date

if 'transactions' not in st.session_state:
    st.session_state['transactions'] = pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])

st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
st.title("🐖 HAMM: Expense Tracker")

page = st.sidebar.radio("Navigation", ["Dashboard", "Add Transaction", "View / Edit", "Analytics", "Budget", "Settings"])

df = st.session_state['transactions']

if page == "Dashboard":
    st.header("📊 Dashboard Overview")
    if df.empty:
        st.info("No transactions yet. Add one in 'Add Transaction'.")
    else:
        income = df[df['Type'] == 'Income']['Amount'].sum()
        expense = df[df['Type'] == 'Expense']['Amount'].sum()
        balance = income - expense

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"${income:,.2f}")
        col2.metric("Total Expenses", f"${expense:,.2f}")
        col3.metric("Current Balance", f"${balance:,.2f}")

        st.subheader("Spending Over Time")
        df['Date'] = pd.to_datetime(df['Date'])
        chart_data = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum().reset_index()
        chart_data['Date'] = chart_data['Date'].astype(str)
        st.line_chart(chart_data, x='Date', y='Amount')

elif page == "Add Transaction":
    st.header("➕ Add Transaction")
    with st.form("add_form", clear_on_submit=True):
        t_date = st.date_input("Date", value=date.today())
        t_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
        t_cat = st.selectbox("Category", ["Food", "Transport", "Salary", "Entertainment", "Other"])
        t_amount = st.number_input("Amount", min_value=0.0, step=0.01)
        t_desc = st.text_input("Description")
        submitted = st.form_submit_button("Add Transaction")

        if submitted:
            new_data = pd.DataFrame([[t_date, t_type, t_cat, t_amount, t_desc]], columns=df.columns)
            st.session_state['transactions'] = pd.concat([df, new_data], ignore_index=True)
            st.success("Transaction added successfully!")

elif page == "View / Edit":
    st.header("📋 View / Edit Transactions")
    if df.empty:
        st.info("No transactions to display.")
    else:
        st.dataframe(df)
        st.write("Total entries:", len(df))

elif page == "Analytics":
    st.header("📈 Spending Analytics")
    if df.empty:
        st.info("Add some transactions first.")
    else:
        st.subheader("Expenses by Category")
        exp_df = df[df['Type'] == 'Expense']
        if not exp_df.empty:
            st.bar_chart(exp_df.groupby('Category')['Amount'].sum())

        st.subheader("Income vs Expense")
        summary = pd.DataFrame({
            'Type': ['Income', 'Expense'],
            'Amount': [df[df['Type']=='Income']['Amount'].sum(), df[df['Type']=='Expense']['Amount'].sum()]
        })
        st.bar_chart(summary.set_index('Type'))

elif page == "Budget":
    st.header("🎯 Budget Tracker")
    budget = st.number_input("Set Monthly Budget ($)", min_value=0.0, step=10.0)
    spent = df[df['Type']=='Expense']['Amount'].sum()
    if budget > 0:
        progress = min(spent / budget, 1.0)
        st.progress(progress)
        st.write(f"You've spent ${spent:,.2f} out of ${budget:,.2f}.")
        if spent > budget:
            st.error("Budget exceeded!")
    else:
        st.info("Set a budget to start tracking.")

elif page == "Settings":
    st.header("⚙️ Settings")
    theme = st.radio("Select Theme", ["Light", "Dark"], horizontal=True)
    currency = st.selectbox("Preferred Currency", ["USD", "IDR", "KRW"])
    st.success(f"Settings saved: Theme - {theme}, Currency - {currency}")
