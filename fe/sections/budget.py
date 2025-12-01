import streamlit as st
import pandas as pd
from datetime import datetime

from services.api import (
    get_budgets,
    get_transactions,
    get_categories,
    create_budget,
    update_budget,
    delete_budget
)


def render():
    st.header("📊 Recurring Budget Planner")

    token = st.session_state.get("jwt")
    user_id = st.session_state.get("user_id")

    if not token:
        st.error("You must log in first.")
        return

    # ============================================================
    # LOAD DATA
    # ============================================================
    budgets = get_budgets(token)
    transactions = get_transactions(token)
    categories = get_categories(token)

    budget_df = pd.DataFrame(budgets)
    tx_df = pd.DataFrame(transactions)
    cat_df = pd.DataFrame(categories)

    # Normalize transaction_date
    tx_df.rename(columns={
        "transaction-date": "transaction_date",
        "transaction_date": "transaction_date",
        "date": "transaction_date"
    }, inplace=True)

    if "transaction_date" not in tx_df.columns:
        st.error("Backend missing 'transaction_date'")
        return

    tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction_date"], errors="coerce")

    # ============================================================
    # STEP 1 — SELECT MONTH & YEAR
    # ============================================================
    st.subheader("📅 Select Month")

    months = {
        1: "January", 2: "February", 3: "March",
        4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September",
        10: "October", 11: "November", 12: "December"
    }

    now = datetime.now()

    selected_month = st.selectbox(
        "Month:",
        list(months.keys()),
        index=now.month - 1,
        format_func=lambda m: months[m]
    )

    selected_year = st.selectbox(
        "Year:",
        list(range(2020, 2035)),
        index=list(range(2020, 2035)).index(now.year)
    )

    st.write(f"Selected: **{months[selected_month]} {selected_year}**")

    # Month start and end boundaries
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        month_end = datetime(selected_year + 1, 1, 1)
    else:
        month_end = datetime(selected_year, selected_month + 1, 1)

    # ============================================================
    # STEP 2 — ADD NEW BUDGET (FOR THIS MONTH)
    # ============================================================
    st.subheader("➕ Add New Budget for This Month")

    category_map = {c["name"]: c["id"] for c in categories}

    default_start = month_start.strftime("%d-%m-%Y")
    default_end = (month_end - pd.Timedelta(days=1)).strftime("%d-%m-%Y")

    with st.form("add_budget"):
        b_category = st.selectbox("Category", list(category_map.keys()))
        b_amount = st.number_input("Budget Amount", min_value=0.0, step=0.01)

        st.write(f"Start Date: **{default_start}**")
        st.write(f"End Date: **{default_end}**")

        submit_budget = st.form_submit_button("Create Budget")

    if submit_budget:
        resp = create_budget(
            token,
            category_id=category_map[b_category],
            budget_amount=b_amount,
            start_date=default_start,
            end_date=default_end
        )

        if "data" in resp:
            st.success("Budget created!")
            st.experimental_rerun()
        else:
            st.error(resp)

    # ============================================================
    # STEP 3 — MONTHLY SUMMARY
    # ============================================================
    st.subheader("📌 Monthly Summary")

    # Normalize budget dates
    budget_df["start_date"] = pd.to_datetime(budget_df["start_date"])
    budget_df["end_date"] = pd.to_datetime(budget_df["end_date"])

    # Filter applicable budgets
    applicable_budget = budget_df[
        (budget_df["start_date"] < month_end) &
        (budget_df["end_date"] >= month_start)
    ]

    budget_for_month = applicable_budget["budget_amount"].sum()

    # Filter transactions for this month
    tx_month = tx_df[
        (tx_df["transaction_date"].dt.month == selected_month) &
        (tx_df["transaction_date"].dt.year == selected_year) &
        (tx_df["type"] == "expense")
    ]

    total_spend = tx_month["amount"].sum()
    remaining = budget_for_month - total_spend

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Budget", f"${budget_for_month:,.2f}")
    c2.metric("Total Spending", f"${total_spend:,.2f}")
    c3.metric("Remaining", f"${remaining:,.2f}")

    # ============================================================
    # STEP 4 — CATEGORY BREAKDOWN
    # ============================================================
    st.subheader("📊 Category Breakdown")

    if not tx_month.empty:
        tx_cat = tx_month.merge(cat_df, left_on="category_id", right_on="id", how="left")
        cat_spend = tx_cat.groupby("name")["amount"].sum().reset_index()
        cat_spend.rename(columns={"name": "Category", "amount": "Spent"}, inplace=True)

        st.dataframe(cat_spend, use_container_width=True)
    else:
        st.info("No transactions for this month.")

    # ============================================================
    # STEP 5 — PROGRESS PER CATEGORY
    # ============================================================
    st.subheader("📌 Progress per Category")

    if not tx_month.empty:
        for _, row in cat_spend.iterrows():
            st.write(f"### {row['Category']}")
            pct = row["Spent"] / budget_for_month if budget_for_month > 0 else 0
            st.progress(min(pct, 1))
            st.caption(f"Spent ${row['Spent']:.2f} of ${budget_for_month:.2f}")

    # ============================================================
    # STEP 6 — EDIT EXISTING BUDGETS
    # ============================================================
    st.subheader("✏️ Edit Existing Budgets")

    if not budget_df.empty:
        edit_df = st.data_editor(
            budget_df.rename(columns={
                "id": "ID",
                "category_id": "Category",
                "budget_amount": "Amount",
                "start_date": "Start",
                "end_date": "End"
            }),
            disabled=["ID", "user_id"],
            use_container_width=True
        )

        if st.button("Save Changes"):
            for idx in edit_df.index:
                old = budget_df.loc[idx]
                new = edit_df.loc[idx]

                if old["budget_amount"] != new["Amount"] or \
                   str(old["start_date"]) != str(new["Start"]) or \
                   str(old["end_date"]) != str(new["End"]):

                    payload = {
                        "budget_amount": float(new["Amount"]),
                        "start_date": pd.to_datetime(new["Start"]).strftime("%d-%m-%Y"),
                        "end_date": pd.to_datetime(new["End"]).strftime("%d-%m-%Y")
                    }

                    update_budget(token, old["id"], payload)

            st.success("Budgets updated!")
            st.experimental_rerun()

    # ============================================================
    # STEP 7 — DELETE BUDGET
    # ============================================================
    st.subheader("🗑 Delete Budget")

    delete_id = st.number_input("Budget ID to delete:", min_value=1, step=1)

    if st.button("Delete Budget"):
        resp = delete_budget(token, delete_id)
        if "message" in resp:
            st.success("Budget deleted.")
            st.experimental_rerun()
        else:
            st.error(resp)
    