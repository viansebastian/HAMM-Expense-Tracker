import streamlit as st 


def render(): 
    if page == "Add Transaction":
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
