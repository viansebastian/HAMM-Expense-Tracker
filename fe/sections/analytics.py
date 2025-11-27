import streamlit as st
import pandas as pd
import plotly.express as px

from services.api import get_transactions, get_categories


# ======================================================
#  ANALYTICS ENGINE
# ======================================================
def compute_analytics(transactions, start_date=None, end_date=None, category=None, tx_type=None):
    df = pd.DataFrame(transactions)

    if df.empty:
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "monthly": [],
            "filtered": []
        }

    # --- Find valid date column ---
    if "transaction_date" in df.columns:
        dc = "transaction_date"
    elif "transaction-date" in df.columns:
        dc = "transaction-date"
    elif "date" in df.columns:
        dc = "date"
    else:
        st.error("Backend returned no valid date field.")
        return

    df["transaction_date"] = pd.to_datetime(df[dc], errors="coerce")

    # --- Apply filters ---
    if start_date:
        df = df[df["transaction_date"].dt.date >= start_date]
    if end_date:
        df = df[df["transaction_date"].dt.date <= end_date]
    if category:
        df = df[df["category_name"] == category]
    if tx_type:
        df = df[df["type"] == tx_type]

    if df.empty:
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "monthly": [],
            "filtered": []
        }

    total_income = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    balance = total_income - total_expense

    # --- Expense Distribution ---
    exp_df = df[df["type"] == "expense"]
    if not exp_df.empty:
        expense_dist = (
            exp_df.groupby("category_name")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
        ).to_dict(orient="records")
    else:
        expense_dist = []

    # --- Monthly Trend ---
    df["month"] = df["transaction_date"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby(["month", "type"])["amount"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="type", values="amount")
        .fillna(0)
        .reset_index()
    ).to_dict(orient="records")

    return {
        "summary": {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "balance": float(balance),
        },
        "expense_dist": expense_dist,
        "monthly": monthly,
        "filtered": df.to_dict(orient="records"),
    }


# ======================================================
#  STREAMLIT UI
# ======================================================
def render():
    st.markdown("""
        <h2 style="text-align:center; margin-bottom:0px;">📊 Analytics & Insights</h2>
        <p style="text-align:center; color:gray; margin-top:-6px;">
            Understand your finances with clean and interactive visual summaries.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # ---------------------------
    # VERIFY LOGIN / JWT
    # ---------------------------
    if "jwt" not in st.session_state or not st.session_state.jwt:
        st.error("You must log in first.")
        return

    token = st.session_state.jwt

    # ---------------------------
    # LOAD DATA
    # ---------------------------
    try:
        tx_res = get_transactions(token)
        cat_res = get_categories(token)

        if tx_res.status_code != 200:
            st.error(f"Failed to fetch transactions: {tx_res.text}")
            return
        if cat_res.status_code != 200:
            st.error(f"Failed to fetch categories: {cat_res.text}")
            return

        transactions = tx_res.json()
        categories = cat_res.json()

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    if not transactions:
        st.warning("No transactions found.")
        return

    # ---------------------------
    # Attach category names
    # ---------------------------
    cat_map = {c["id"]: c["name"] for c in categories}
    for tx in transactions:
        tx["category_name"] = cat_map.get(tx.get("category_id"), "Uncategorized")

    df_all = pd.DataFrame(transactions)

    # normalize date field
    if "transaction_date" in df_all.columns:
        dc = "transaction_date"
    elif "transaction-date" in df_all.columns:
        dc = "transaction-date"
    else:
        dc = "date"

    df_all["transaction_date"] = pd.to_datetime(df_all[dc], errors="coerce")

    # ======================================================
    #  FILTER BAR UI
    # ======================================================
    st.markdown("""
    <div style="padding:18px; border-radius:12px; background:#fafafa; 
                border:1px solid #eee; margin-bottom:25px;">
        <h4 style="margin-top:0;">🔍 Filters</h4>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        min_date = df_all["transaction_date"].min().date()
        max_date = df_all["transaction_date"].max().date()

        date_range = st.date_input(
            "📅 Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
        )

        if not isinstance(date_range, tuple) or len(date_range) != 2:
            st.error("Please select a valid start and end date.")
            st.stop()

        start_date, end_date = date_range

        categories_list = ["All"] + sorted([c["name"] for c in categories])
        type_list = ["All", "Income", "Expense"]

        col3, col4 = st.columns(2)
        with col3:
            selected_category = st.selectbox("📂 Category", categories_list)
        with col4:
            tx_type = st.selectbox("💰 Transaction Type", type_list)

    if selected_category == "All":
        selected_category = None
    if tx_type == "All":
        tx_type = None

    # ======================================================
    #  RUN ANALYTICS
    # ======================================================
    results = compute_analytics(
        transactions,
        start_date=start_date,
        end_date=end_date,
        category=selected_category,
        tx_type=tx_type,
    )

    summary = results["summary"]
    expense_dist = results["expense_dist"]
    monthly = results["monthly"]
    filtered = results["filtered"]

    # ======================================================
    # SUMMARY CARDS
    # ======================================================
    st.subheader("📌 Summary")
    st.write("")

    c1, c2, c3 = st.columns(3)

    def card(value, label):
        st.markdown(f"""
            <div style="
                background:#fdfdfd;
                padding:18px;
                border-radius:12px;
                border:1px solid #e6e6e6;
                box-shadow:0px 1px 2px rgba(0,0,0,0.05);
                text-align:center;">
                <div style="font-size:26px; font-weight:600;">{value:,.2f}</div>
                <div style="color:gray; margin-top:4px;">{label}</div>
            </div>
        """, unsafe_allow_html=True)

    with c1: card(summary["total_income"], "Total Income")
    with c2: card(summary["total_expense"], "Total Expense")
    with c3: card(summary["balance"], "Balance")

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # EXPENSE PIE CHART
    # ======================================================
    st.subheader("🥧 Expense Distribution")

    if expense_dist:
        df_exp = pd.DataFrame(expense_dist)
        fig_pie = px.pie(df_exp, names="category_name", values="amount", hole=0.45)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense data found.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # MONTHLY TREND CHART
    # ======================================================
    st.subheader("📈 Monthly Income vs Expense")

    if monthly:
        df_month = pd.DataFrame(monthly)
        df_month["income"] = df_month.get("income", 0)
        df_month["expense"] = df_month.get("expense", 0)

        fig_line = px.line(df_month, x="month", y=["income", "expense"], markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No monthly data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # TABLE
    # ======================================================
    with st.expander("📄 Filtered Transactions", expanded=True):
        if filtered:
            st.dataframe(pd.DataFrame(filtered), use_container_width=True, height=350)
        else:
            st.warning("No matching transactions.")
