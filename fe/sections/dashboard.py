import streamlit as st 
import pandas as pd


def render():
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