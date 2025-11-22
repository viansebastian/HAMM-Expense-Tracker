import streamlit as st 


def render():
    if page == "Analytics":
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