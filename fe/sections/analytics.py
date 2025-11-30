import streamlit as st
import pandas as pd
import plotly.express as px
# Assuming services.api is the correct path for your API client functions
from services.api import get_transactions, get_categories, predict_by_type
from datetime import date, timedelta


# ======================================================
#  ANALYTICS ENGINE (Local Data Processing)
# ======================================================
def compute_analytics(transactions, start_date=None, end_date=None, category=None, tx_type=None):
    """
    Computes key financial analytics (summary, distribution, monthly trend) 
    based on the filtered DataFrame.
    """
    df = pd.DataFrame(transactions)

    if df.empty:
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "monthly": [],
            "filtered": []
        }

    # --- Find valid date column ---
    dc = None
    if "transaction_date" in df.columns:
        dc = "transaction_date"
    elif "transaction-date" in df.columns:
        dc = "transaction-date"
    elif "date" in df.columns:
        dc = "date"
    
    if dc is None:
        # Fallback for data quality issues
        st.error("Backend returned no valid date field. Cannot apply date filters.")
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "monthly": [],
            "filtered": []
        }

    # Convert the identified date column to datetime objects
    df["transaction_date"] = pd.to_datetime(df[dc], errors="coerce")
    
    # Drop rows where date conversion failed
    df = df.dropna(subset=['transaction_date'])

    # --- Apply filters ---
    if start_date:
        df = df[df["transaction_date"].dt.date >= start_date]
    if end_date:
        df = df[df["transaction_date"].dt.date <= end_date]
    if category:
        df = df[df["category_name"] == category]
    if tx_type:
        # Filter transactions based on type (must match 'income' or 'expense')
        df = df[df["type"].str.lower() == tx_type.lower()] 

    if df.empty:
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "monthly": [],
            "filtered": []
        }

    # Calculate summary metrics
    total_income = df[df["type"].str.lower() == "income"]["amount"].sum()
    total_expense = df[df["type"].str.lower() == "expense"]["amount"].sum()
    balance = total_income - total_expense

    # --- Expense Distribution ---
    exp_df = df[df["type"].str.lower() == "expense"]
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
#  PREDICTION SECTION HELPER
# ======================================================

def fetch_prediction(token, tx_type):
    """Fetches prediction data and handles API response."""
    try:
        # tx_type is passed as 'income' or 'expense'
        res = predict_by_type(token, tx_type.lower()) 
        if res.status_code == 200:
            return res.json(), None
        else:
            return None, f"API Error ({res.status_code}): {res.text}"
    except Exception as e:
        return None, f"Connection Error: {e}"

def render_predictions_section(token):
    """Renders the AI prediction section."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.header("🧠 AI Predictions (Next 30 Days)")
    st.markdown("""
        <p style="color:gray; margin-top:-6px;">
            Based on your historical data, here are projected totals for the upcoming month.
        </p>
    """, unsafe_allow_html=True)
    
    col_inc, col_exp = st.columns(2)

    # --- Fetch Income Prediction ---
    with col_inc:
        st.subheader("Projected Income")
        income_pred, income_err = fetch_prediction(token, "income")
        
        if income_err:
            st.error(f"Income Prediction Failed: {income_err}")
        elif income_pred and isinstance(income_pred, dict) and 'predicted_total' in income_pred:
            predicted_amount = income_pred.get('predicted_total', 0)
            st.markdown(f"""
                <div style="
                    background:#f1fdf1;
                    padding:18px;
                    border-radius:12px;
                    border:1px solid #c8e6c9;
                    text-align:center;">
                    <div style="font-size:32px; font-weight:700; color:#22c55e;">
                        Rp. {predicted_amount:,.2f}
                    </div>
                    <div style="color:gray; margin-top:4px;">Estimated Income</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No income prediction data available.")


    # --- Fetch Expense Prediction ---
    with col_exp:
        st.subheader("Projected Expense")
        expense_pred, expense_err = fetch_prediction(token, "expense")

        if expense_err:
            st.error(f"Expense Prediction Failed: {expense_err}")
        elif expense_pred and isinstance(expense_pred, dict) and 'predicted_total' in expense_pred:
            predicted_amount = expense_pred.get('predicted_total', 0)
            st.markdown(f"""
                <div style="
                    background:#fef5f5;
                    padding:18px;
                    border-radius:12px;
                    border:1px solid #fcc6c6;
                    text-align:center;">
                    <div style="font-size:32px; font-weight:700; color:#ef4444;">
                        Rp. {predicted_amount:,.2f}
                    </div>
                    <div style="color:gray; margin-top:4px;">Estimated Expense</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No expense prediction data available.")
            
    st.markdown("<br>", unsafe_allow_html=True)


# ======================================================
#  STREAMLIT UI
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
    # LOAD DATA FROM SESSION STATE (NO REDUNDANT API CALLS)
    # ---------------------------
    
    # Check if data exists in session state (must be initialized by state_manager.py)
    if "transactions" not in st.session_state or "categories" not in st.session_state:
        st.error("Data not loaded into session state. Ensure `load_all_user_data()` runs on startup.")
        return
    
    # Unwrap and check Response objects
    tx_res = st.session_state.transactions
    cat_res = st.session_state.categories
    
    try:
        if tx_res.status_code != 200:
            st.error(f"Failed to fetch transactions from API cache: {tx_res.text}")
            return
        if cat_res.status_code != 200:
            st.error(f"Failed to fetch categories from API cache: {cat_res.text}")
            return

        transactions = tx_res.json()
        categories = cat_res.json()

    except Exception as e:
        st.error(f"Error processing cached data: {e}")
        return

    if not transactions:
        st.warning("No transactions found.")
        # Render prediction section even if no transactions exist
        render_predictions_section(token) 
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
    
    # Drop rows where date conversion failed
    df_all = df_all.dropna(subset=['transaction_date'])

    # ======================================================
    #  FILTER BAR UI (Using actual transaction dates for min/max constraint)
    # ======================================================
    st.markdown("""
    <div style="padding:18px; border-radius:12px; background:#fafafa; 
                 border:1px solid #eee; margin-bottom:25px;">
        <h4 style="margin-top:0;">🔍 Filters</h4>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        # Ensure we have valid dates before calculating min/max
        if df_all.empty or df_all["transaction_date"].isnull().all():
            min_date_data = date.today() - timedelta(days=365)
            max_date_data = date.today()
        else:
            min_date_data = df_all["transaction_date"].min().date()
            max_date_data = df_all["transaction_date"].max().date()
        
        # Default start date calculation
        default_start = max_date_data - timedelta(days=30)
        if default_start < min_date_data:
            default_start = min_date_data
            
        # Ensure date selection is valid
        if min_date_data > max_date_data:
            min_date_data = max_date_data - timedelta(days=1)
        
        date_range_value = (default_start, max_date_data)

        date_range = st.date_input(
            "📅 Date Range",
            value=date_range_value,
            min_value=min_date_data,
            max_value=max_date_data,
            format="YYYY-MM-DD",
        )

        if not isinstance(date_range, tuple) or len(date_range) != 2:
            st.error("Please select a valid start and end date.")
            st.stop()

        start_date, end_date = date_range

        # Streamlit handles the constraint that start_date <= end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

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
    elif tx_type in ["Income", "Expense"]:
        tx_type = tx_type.lower()
        

    # ======================================================
    #  RUN ANALYTICS
    # ======================================================
    # Use the transactions list loaded from session state
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

    def card(value, label, color="#000000"):
        st.markdown(f"""
            <div style="
                background:#fdfdfd;
                padding:18px;
                border-radius:12px;
                border:1px solid #e6e6e6;
                box-shadow:0px 1px 2px rgba(0,0,0,0.05);
                text-align:center;">
                <div style="font-size:26px; font-weight:600; color:{color};">Rp. {value:,.2f}</div>
                <div style="color:gray; margin-top:4px;">{label}</div>
            </div>
        """, unsafe_allow_html=True)

    with c1: 
        card(summary["total_income"], "Total Income", "#22c55e")  # Green
    with c2: 
        card(summary["total_expense"], "Total Expense", "#ef4444")  # Red
    with c3: 
        card(summary["balance"], "Balance", "#3b82f6")  # Blue

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # EXPENSE PIE CHART
    # ======================================================
    st.subheader("🥧 Expense Distribution")

    if expense_dist:
        df_exp = pd.DataFrame(expense_dist)
        df_exp['amount'] = pd.to_numeric(df_exp['amount'], errors='coerce') 
        fig_pie = px.pie(df_exp, names="category_name", values="amount", hole=0.45)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense data found in the selected range.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # MONTHLY TREND CHART
    # ======================================================
    st.subheader("📈 Monthly Income vs Expense")

    if monthly:
        df_month = pd.DataFrame(monthly)
        df_month["income"] = pd.to_numeric(df_month.get("income", 0), errors='coerce')
        df_month["expense"] = pd.to_numeric(df_month.get("expense", 0), errors='coerce')

        fig_line = px.line(df_month, x="month", y=["income", "expense"], markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No monthly data available in the selected range.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # AI PREDICTIONS
    # ======================================================
    # This section must remain as it calls the predict_by_type API directly, 
    # which is not cached by load_all_user_data().
    render_predictions_section(token)
    
    # ======================================================
    # TABLE
    # ======================================================
    with st.expander("📄 Filtered Transactions", expanded=True):
        if filtered:
            display_df = pd.DataFrame(filtered)
            if 'transaction_date' in display_df.columns:
                 # Drop the temporary normalized date for display, if it exists
                 display_df = display_df.drop(columns=['transaction_date'], errors='ignore')
            st.dataframe(display_df, use_container_width=True, height=350)
        else:
            st.warning("No matching transactions.")