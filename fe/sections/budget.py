import streamlit as st
import pandas as pd
from datetime import datetime
from services.api import (
    get_budgets,
    get_transactions,
    get_categories,
    create_budget,
    update_budget,
    delete_budget,
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def normalize_to_list(response):
    """
    Standardizes backend responses into a list of dictionaries.
    Handles: list, dict with 'data' key, or dict with a single list value.
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


def _extract_list_from_response(resp, label: str):
    """
    Safe wrapper for API responses. 
    Checks status codes and JSON parsing to prevent app crashes.
    """
    if resp is None:
        st.error(f"Failed to load {label}: no response from API.")
        return []

    text = resp.text or ""
    status = resp.status_code

    # Try parsing JSON
    try:
        data = resp.json()
    except Exception:
        # If success (2xx) but empty body, return empty list
        if status < 400 and not text.strip():
            return []
        # If error, show raw text
        st.error(
            f"Failed to parse JSON for {label}. "
            f"Status code: {status}. Raw response: {text[:200]}"
        )
        return []

    # Handle API-level errors (400, 401, 500)
    if status >= 400:
        if isinstance(data, dict):
            msg = data.get("error") or data.get("msg") or data
        else:
            msg = data
        st.error(f"Error fetching {label}: {msg}")
        return []

    # Success
    return normalize_to_list(data)


# ==========================================
# MAIN PAGE RENDER
# ==========================================

def render():
    st.header("💰 Monthly Budget Planner")

    token = st.session_state.get("jwt")

    if not token:
        st.error("You must log in first.")
        return

    # 1. LOAD DATA SAFELY
    budgets_resp = get_budgets(token)
    tx_resp = get_transactions(token)
    cat_resp = get_categories(token)

    budgets = _extract_list_from_response(budgets_resp, "budgets")
    transactions = _extract_list_from_response(tx_resp, "transactions")
    categories = _extract_list_from_response(cat_resp, "categories")

    budget_df = pd.DataFrame(budgets)
    tx_df = pd.DataFrame(transactions)
    cat_df = pd.DataFrame(categories)

    # Map ID -> Category Name for easy lookup
    cat_map = {row['id']: row['name'] for _, row in cat_df.iterrows()} if not cat_df.empty else {}

    # Ensure necessary columns exist in Budget DF
    for col in ["id", "budget_amount", "start_date", "end_date", "category_id", "created_at", "updated_at"]:
        if col not in budget_df.columns:
            budget_df[col] = None

    # Ensure necessary columns exist in Transaction DF
    if "amount" not in tx_df.columns:
        tx_df["amount"] = 0.0
    else:
        tx_df["amount"] = pd.to_numeric(tx_df["amount"], errors="coerce")

    # Handle Transaction Date mapping
    if "transaction-date" in tx_df.columns:
        tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction-date"], errors="coerce")
    else:
        tx_df["transaction_date"] = pd.NaT

    # ==========================================
    # STEP 1: SELECT MONTH
    # ==========================================
    st.subheader("📅 Select Month")

    months = {
        1: "January", 2: "February", 3: "March",
        4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September",
        10: "October", 11: "November", 12: "December"
    }

    now = datetime.now()
    col_m, col_y = st.columns(2)
    
    with col_m:
        selected_month = st.selectbox(
            "Month",
            list(months.keys()),
            index=now.month - 1,
            format_func=lambda m: months[m]
        )
    
    with col_y:
        selected_year = st.selectbox(
            "Year",
            list(range(2020, 2035)),
            index=list(range(2020, 2035)).index(now.year)
        )

    # Calculate start and end of selected month
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        month_end = datetime(selected_year + 1, 1, 1)
    else:
        month_end = datetime(selected_year, selected_month + 1, 1)

    # ==========================================
    # STEP 2: ADD NEW BUDGET
    # ==========================================
    with st.expander("➕ Add New Budget", expanded=False):
        # Create a reverse map for the dropdown (Name -> ID)
        cat_options = {name: cid for cid, name in cat_map.items()}
        
        with st.form("add_budget_form"):
            if cat_options:
                b_cat_name = st.selectbox("Category", list(cat_options.keys()))
            else:
                st.warning("No categories found. Please create categories first.")
                b_cat_name = None

            b_amount = st.number_input("Budget Amount", min_value=0.0, step=10.0)
            
            # Default dates: 1st of month to last of month
            d_start_str = month_start.strftime("%d-%m-%Y")
            d_end_obj = month_end - pd.Timedelta(days=1)
            d_end_str = d_end_obj.strftime("%d-%m-%Y")

            st.caption(f"Budget applies to: **{d_start_str}** until **{d_end_str}**")
            
            submitted = st.form_submit_button("Create Budget")

            if submitted:
                if not b_cat_name:
                    st.error("Select a category.")
                elif b_amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    cat_id = cat_options[b_cat_name]
                    resp = create_budget(token, cat_id, b_amount, d_start_str, d_end_str)
                    
                    if resp.status_code < 400:
                        st.success("Budget created successfully!")
                        st.rerun() # Refresh page to show new data
                    else:
                        st.error(f"Error: {resp.text}")

    # ==========================================
    # PREPARE DATA FOR ANALYSIS
    # ==========================================
    # normalize dates for filtering
    for col in ["start_date", "end_date"]:
        budget_df[col] = pd.to_datetime(budget_df[col], errors="coerce")

    # Filter Budgets for this month
    active_budgets = budget_df[
        (budget_df["start_date"] < month_end) &
        (budget_df["end_date"] >= month_start)
    ].copy()

    # Filter Transactions for this month (Expenses only)
    tx_month = pd.DataFrame()
    if not tx_df.empty:
        # Check if type column exists, otherwise assume all are expenses
        is_expense = tx_df["type"].str.lower() == "expense" if "type" in tx_df.columns else True
        
        tx_month = tx_df[
            is_expense &
            (tx_df["transaction_date"] >= month_start) &
            (tx_df["transaction_date"] < month_end)
        ]

    # ==========================================
    # STEP 3: MONTHLY SUMMARY
    # ==========================================
    st.subheader("📌 Monthly Summary")

    total_budget_val = active_budgets["budget_amount"].sum()
    total_spent_val = tx_month["amount"].sum() if not tx_month.empty else 0.0
    remaining_val = total_budget_val - total_spent_val

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Budget", f"${total_budget_val:,.2f}")
    m2.metric("Total Spent", f"${total_spent_val:,.2f}", delta=f"{-total_spent_val:,.2f}", delta_color="inverse")
    m3.metric("Remaining", f"${remaining_val:,.2f}", delta_color="normal")

# ==========================================
    # STEP 4: CATEGORY BREAKDOWN (With % Bars)
    # ==========================================
    st.subheader("📊 Category Breakdown")

    if not active_budgets.empty or not tx_month.empty:
        # Group Budgets by Category ID
        b_grouped = active_budgets.groupby("category_id")["budget_amount"].sum().reset_index()
        
        # Group Expenses by Category ID
        if not tx_month.empty:
            s_grouped = tx_month.groupby("category_id")["amount"].sum().reset_index()
        else:
            s_grouped = pd.DataFrame(columns=["category_id", "amount"])

        # Merge them
        merged = pd.merge(b_grouped, s_grouped, on="category_id", how="outer").fillna(0)
        
        # Add Category Name
        merged["Category"] = merged["category_id"].map(cat_map).fillna("Unknown")

        # --- FIX STARTS HERE ---
        # Calculate Percentage as 0-100 instead of 0-1
        merged["ratio"] = merged.apply(lambda x: (x["amount"] / x["budget_amount"] * 100) if x["budget_amount"] > 0 else 0, axis=1)
        
        # Clip max value to 100 so the bar doesn't break if you overspend
        merged["ratio"] = merged["ratio"].clip(0, 100) 

        # Prepare final display table
        display_df = merged[["Category", "budget_amount", "amount", "ratio"]].copy()
        display_df.rename(columns={"budget_amount": "Budget", "amount": "Spent"}, inplace=True)

        st.dataframe(
            display_df,
            column_config={
                "Budget": st.column_config.NumberColumn(format="$%.2f"),
                "Spent": st.column_config.NumberColumn(format="$%.2f"),
                "ratio": st.column_config.ProgressColumn(
                    "Used %",
                    help="Percentage of budget used",
                    format="%.1f%%",   # Shows "50.5%"
                    min_value=0,
                    max_value=100,     # Scale is now 0-100
                ),
            },
            use_container_width=True,
            hide_index=True
        )
        # --- FIX ENDS HERE ---
    else:
        st.info("No activity found for this month.")
# ==========================================
    # STEP 5: EDIT BUDGETS
    # ==========================================
    st.subheader("✏️ Edit Budgets")
    
    if not budget_df.empty:
        # Prepare DataFrame for Editor
        edit_prep = budget_df.copy()
        edit_prep["Category Name"] = edit_prep["category_id"].map(cat_map).fillna("Unknown ID")
        
        # Configure columns
        # We hide ID but keep it in data so we know what to update
        edited_df = st.data_editor(
            edit_prep,
            column_order=["Category Name", "budget_amount", "start_date", "end_date"],
            # --- CHANGE HERE: List columns that cannot be edited ---
            disabled=["Category Name", "start_date", "end_date"], 
            column_config={
                "Category Name": st.column_config.TextColumn("Category"),
                "budget_amount": st.column_config.NumberColumn(
                    "Budget", 
                    min_value=0, 
                    step=10,
                    required=True
                ),
                "start_date": st.column_config.DateColumn("Start Date", format="DD-MM-YYYY"),
                "end_date": st.column_config.DateColumn("End Date", format="DD-MM-YYYY"),
            },
            hide_index=True,
            use_container_width=True,
            key="budget_edit_table"
        )

        if st.button("Save Changes"):
            changes_made = 0
            # Iterate through the edited dataframe to find differences
            for index, row in edited_df.iterrows():
                original_row = budget_df.loc[index]
                
                # Compare values
                new_amt = float(row["budget_amount"])
                orig_amt = float(original_row["budget_amount"])

                # Since dates are disabled, we only really check if amount changed
                # But we still send dates back to the API to be safe
                if new_amt != orig_amt:
                    
                    # Prepare the payload
                    # We grab dates from the row (which are unchanged) to satisfy the API
                    new_start = pd.to_datetime(row["start_date"]).strftime("%d-%m-%Y")
                    new_end = pd.to_datetime(row["end_date"]).strftime("%d-%m-%Y")

                    payload = {
                        "budget_amount": new_amt,
                        "start_date": new_start,
                        "end_date": new_end
                    }
                    
                    update_budget(token, row["id"], payload)
                    changes_made += 1
            
            if changes_made > 0:
                st.success(f"Updated {changes_made} budgets successfully!")
                st.rerun()
            else:
                st.info("No changes detected.")
    # ==========================================
    # STEP 6: DELETE BUDGET
    # ==========================================
    st.subheader("🗑 Delete Budget")

    if not budget_df.empty:
        # Create user-friendly labels for the dropdown
        # Format: "Groceries - $500 (Starts: 2023-01-01)"
        delete_map = {}
        for idx, row in budget_df.iterrows():
            c_name = cat_map.get(row['category_id'], 'Unknown')
            amt = row['budget_amount']
            s_date = row['start_date'].strftime("%Y-%m-%d") if pd.notnull(row['start_date']) else "?"
            label = f"{c_name} — Rp.{amt:,.0f} (Starts: {s_date})"
            delete_map[label] = row['id']

        selected_label = st.selectbox("Select budget to delete", list(delete_map.keys()))

        if st.button("Delete Selected Budget", type="primary"):
            budget_id_to_delete = delete_map[selected_label]
            resp = delete_budget(token, budget_id_to_delete)
            
            if resp.status_code < 400:
                st.success("Budget deleted!")
                st.rerun()
            else:
                st.error(f"Failed to delete: {resp.text}")
    else:
        st.write("No budgets to delete.")