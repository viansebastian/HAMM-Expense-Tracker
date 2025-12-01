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

def normalize_to_list(response):
    """
    Mengubah bentuk response backend apa pun menjadi list of dicts:
    - list langsung → return as-is
    - dict dengan key "data" → return data
    - dict dengan 1 list di dalamnya → return list tsb
    - dict kosong atau error → return []
    """
    if response is None:
        return []

    if isinstance(response, list):
        return response

    if isinstance(response, dict):
        # Case: {"data": [...]}
        if "data" in response and isinstance(response["data"], list):
            return response["data"]

        # Case: {"budgets": [...]}, {"items": [...]}, etc.
        for v in response.values():
            if isinstance(v, list):
                return v

        # Case: error or not a list
        return []

    return []


def render():
    st.header("💰 Monthly Budget Planner")

    token = st.session_state.get("jwt")

    if not token:
        st.error("You must log in first.")
        return

    # ============================================================
    # LOAD DATA (TANPA ERROR MESKI BACKEND TIDAK KONSISTEN)
    # ============================================================
    raw_budgets = get_budgets(token)
    raw_tx = get_transactions(token)
    raw_cat = get_categories(token)

    budgets = normalize_to_list(raw_budgets)
    transactions = normalize_to_list(raw_tx)
    categories = normalize_to_list(raw_cat)

    budget_df = pd.DataFrame(budgets)
    tx_df = pd.DataFrame(transactions)
    cat_df = pd.DataFrame(categories)

    # Kalau kolom tidak ada → buat kolom kosong agar tidak error
    for df, col in [(budget_df, "budget_amount"), (budget_df, "start_date"), (budget_df, "end_date")]:
        if col not in df.columns:
            df[col] = None

    if "amount" in tx_df.columns:
        tx_df["amount"] = pd.to_numeric(tx_df["amount"], errors="coerce")
    else:
        tx_df["amount"] = 0

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

    month_start = datetime(selected_year, selected_month, 1)
    month_end = (
        datetime(selected_year + 1, 1, 1)
        if selected_month == 12 else
        datetime(selected_year, selected_month + 1, 1)
    )

    # ============================================================
    # STEP 2 — ADD NEW BUDGET
    # ============================================================
    st.subheader("➕ Add New Budget")

    category_map = {c.get("name", f"Cat{idx}"): c.get("id") for idx, c in enumerate(categories)}

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
        st.success("Budget created!")
        st.experimental_rerun()

    # ============================================================
    # STEP 3 — MONTHLY SUMMARY
    # ============================================================
    st.subheader("📌 Monthly Summary")

    # Normalize dates
    budget_df["start_date"] = pd.to_datetime(budget_df["start_date"], errors="coerce")
    budget_df["end_date"] = pd.to_datetime(budget_df["end_date"], errors="coerce")

    applicable_budget = budget_df[
        (budget_df["start_date"] < month_end) &
        (budget_df["end_date"] >= month_start)
    ]

    budget_for_month = applicable_budget["budget_amount"].sum()

    # Expenses only
    if "type" in tx_df.columns:
        tx_expense = tx_df[tx_df["type"] == "expense"]
    else:
        tx_expense = pd.DataFrame(columns=tx_df.columns)

    total_spend = tx_expense["amount"].sum()
    remaining = budget_for_month - total_spend

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Budget", f"${budget_for_month:,.2f}")
    c2.metric("Total Spending", f"${total_spend:,.2f}")
    c3.metric("Remaining", f"${remaining:,.2f}")

    # ============================================================
    # STEP 4 — CATEGORY BREAKDOWN
    # ============================================================
    st.subheader("📊 Category Breakdown")

    if not tx_expense.empty:
        tx_cat = tx_expense.merge(cat_df, left_on="category_id", right_on="id", how="left")
        cat_spend = tx_cat.groupby(tx_cat["name"].fillna("Unknown"))["amount"].sum().reset_index()
        cat_spend.rename(columns={"name": "Category", "amount": "Spent"}, inplace=True)
        st.dataframe(cat_spend, use_container_width=True)
    else:
        st.info("No spending this month.")

    # ============================================================
    # STEP 5 — EDIT BUDGET
    # ============================================================
    st.subheader("✏️ Edit Existing Budgets")

    if not budget_df.empty:
        display_df = budget_df.copy()
        display_df.rename(columns={
            "id": "ID",
            "category_id": "Category",
            "budget_amount": "Amount",
            "start_date": "Start",
            "end_date": "End"
        }, inplace=True)

        edit_df = st.data_editor(
            display_df,
            disabled=["ID"],
            use_container_width=True
        )

        if st.button("Save Changes"):
            for idx in edit_df.index:
                old = budget_df.loc[idx]
                new = edit_df.loc[idx]

                updated = {
                    "budget_amount": float(new["Amount"]),
                    "start_date": pd.to_datetime(new["Start"]).strftime("%d-%m-%Y"),
                    "end_date": pd.to_datetime(new["End"]).strftime("%d-%m-%Y")
                }
                update_budget(token, old["id"], updated)

            st.success("Updated!")
            st.experimental_rerun()

    # ============================================================
    # STEP 6 — DELETE
    # ============================================================
    st.subheader("🗑 Delete Budget")

    delete_id = st.number_input("Budget ID to delete:", min_value=1, step=1)
    if st.button("Delete Budget"):
        delete_budget(token, delete_id)
        st.success("Deleted!")
        st.experimental_rerun()
