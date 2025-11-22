import streamlit as st 


def render(): 
    if page == "Budget":
        st.header("🎯 Budget Tracker")
        budget = st.number_input("Set Monthly Budget (Rp.)", min_value=0.0, step=10.0)
        spent = df[df['Type']=='Expense']['Amount'].sum()
        if budget > 0:
            progress = min(spent / budget, 1.0)
            st.progress(progress)
            st.write(f"You've spent ${spent:,.2f} out of ${budget:,.2f}.")
            if spent > budget:
                st.error("Budget exceeded!")
        else:
            st.info("Set a budget to start tracking.")