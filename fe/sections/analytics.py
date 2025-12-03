import streamlit as st
import pandas as pd
import plotly.express as px
from services.api import get_transactions, get_categories, predict_by_type
from datetime import date, timedelta


# ======================================================
# HELPER FUNCTIONS
# ======================================================

def format_currency(amount):
    """Formats a number as currency in Rupiah."""
    # Ensure amount is treated as a float or int before formatting
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        amount = 0.0
        
    return f"Rp{amount:,.2f}"

def get_valid_date_column(df):
    """Identifies the transaction date column from possible names."""
    for col in ["transaction_date", "transaction-date", "date"]:
        if col in df.columns:
            return col
    return None

def preprocess_df(df):
    """Converts the date column to datetime and drops invalid rows."""
    dc = get_valid_date_column(df)
    if not dc:
        st.error("Backend returned no valid date field.")
        return pd.DataFrame()
        
    df["transaction_date"] = pd.to_datetime(df[dc], errors="coerce")
    return df.dropna(subset=['transaction_date'])

# ======================================================
# ANALYTICS ENGINE (Local Data Processing)
# ======================================================
def compute_monthly_trend(transactions):
    """
    Computes monthly income vs expense trend from ALL transactions, 
    ensuring chronological order.
    """
    df = pd.DataFrame(transactions)
    if df.empty:
        return []

    df = preprocess_df(df)
    if df.empty:
        return []

    # 1. Create a sortable Period object column
    df["month_period"] = df["transaction_date"].dt.to_period("M")
    # 2. Create the display string column (e.g., "2023-11")
    df["month"] = df["month_period"].astype(str)
    
    monthly_df = (
        df.groupby(["month_period", "month", "type"])["amount"]
        .sum()
        .reset_index()
    )
    
    # Pivot the data
    monthly_pivoted_df = (
        monthly_df.pivot(index=["month_period", "month"], columns="type", values="amount")
        .fillna(0)
        .reset_index()
    )
    
    # 3. Explicitly sort by the Period column (guarantees chronological order)
    monthly_pivoted_df = monthly_pivoted_df.sort_values(by="month_period")

    # 4. Remove the Period column before returning
    monthly_pivoted_df = monthly_pivoted_df.drop(columns=["month_period"])

    return monthly_pivoted_df.to_dict(orient="records")


def compute_filtered_data(transactions, start_date=None, end_date=None, category=None, tx_type=None):
    """
    Computes key financial analytics (summary, expense distribution) 
    based ONLY on the filtered transactions.
    """
    df = pd.DataFrame(transactions)
    
    if df.empty:
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "filtered": []
        }

    df = preprocess_df(df)
    if df.empty:
        return {
            "summary": {"total_income": 0, "total_expense": 0, "balance": 0},
            "expense_dist": [],
            "filtered": []
        }

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

    # Keep only the columns needed for the detailed expense table
    df_filtered_output = df.to_dict(orient="records")

    return {
        "summary": {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "balance": float(balance),
        },
        "expense_dist": expense_dist,
        "filtered": df_filtered_output,
    }


# ======================================================
# NEW AI PREDICTION SECTION
# ======================================================

def render_predictions_section_new(token):
    """Renders the advanced AI prediction section with line charts."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:18px; border-radius:12px; background:#fafafa; border:1px solid #eee; margin-bottom:25px;">
            <h3 style="margin-top:0;">🔮 2-Month Transaction Prediction (AI) </h3>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <p style="color:gray; margin-top:-6px;">
            Based on your historical monthly data, here are projected totals for the upcoming two months.
        </p>
    """, unsafe_allow_html=True)
    
    pred_col1, pred_col2 = st.columns(2)

    # Helper function to fetch and display predictions
    def fetch_and_display_prediction(tx_type, col):
        with col:
            st.markdown(f"##### {'➕' if tx_type == 'income' else '➖'} **{tx_type.capitalize()}** Prediction")
            
            # Predict by type API call
            predict_response = predict_by_type(token, tx_type) 
            
            if predict_response.status_code == 200:
                pred_data = predict_response.json()
                
                # Prepare data for charting
                # Format history: [['202501', amount], ['202502', amount], ...]
                if not pred_data.get('history'):
                     st.info(f"{tx_type.capitalize()} Prediction: History data is empty.")
                     return
                     
                history_df = pd.DataFrame(pred_data['history'], columns=['Month_Code', 'Amount'])
                
                # Create readable month labels (e.g., '2025-01')
                history_df['Month'] = history_df['Month_Code'].astype(str).str.slice(0, 4) + '-' + history_df['Month_Code'].astype(str).str.slice(4)
                
                # Create labels for prediction months
                last_month_code = history_df['Month_Code'].iloc[-1]
                last_year = int(str(last_month_code)[:4])
                last_month = int(str(last_month_code)[4:])
                
                # Simple logic to get the next 2 month labels
                def get_next_month_label(y, m, offset):
                    m = m + offset
                    y_offset = 0
                    while m > 12:
                        y_offset += 1
                        m -= 12
                    y += y_offset
                    return f"{y}-{m:02d} (Predicted)"
                
                # Check if predicted_next_months is available and has 2 values
                predicted_next_months = pred_data.get('predicted_next_months', [0, 0])
                if len(predicted_next_months) < 2:
                    st.warning(f"{tx_type.capitalize()} Prediction: Prediction data incomplete.")
                    return
                
                next_months_labels = [
                    get_next_month_label(last_year, last_month, 1),
                    get_next_month_label(last_year, last_month, 2)
                ]
                
                prediction_df = pd.DataFrame({
                    'Month': next_months_labels,
                    'Amount': predicted_next_months
                })
                
                # Combine historical and predicted data
                final_pred_df = pd.concat([history_df[['Month', 'Amount']], prediction_df])
                final_pred_df.set_index('Month', inplace=True)
                
                # Use st.line_chart to display the trend
                st.line_chart(final_pred_df['Amount'])
                
                # Display the next month's predictions in a caption
                st.markdown(
                    f"""
                    <p style="font-size:18px; font-weight:500; margin-top:0;">
                        Next 2 months estimates: {format_currency(predicted_next_months[0])} 
                        and {format_currency(predicted_next_months[1])}
                    </p>
                    """,
                    unsafe_allow_html=True
                )

            
            elif predict_response.status_code == 400:
                # Backend returns 400 if data is less than 3 months
                st.warning(f"{tx_type.capitalize()} Prediction: Insufficient data (Need > 3 months).")
            else:
                st.info(f"{tx_type.capitalize()} Prediction not available at the moment. Status: {predict_response.status_code}")

    # Call function for Income and Expense
    fetch_and_display_prediction("income", pred_col1)
    fetch_and_display_prediction("expense", pred_col2)
    st.markdown("<br>", unsafe_allow_html=True)

# ======================================================
# STREAMLIT UI
# ======================================================
def render():
    st.markdown("""
        <h2 style="margin-bottom:0px;">📊 Analytics & Insights</h2>
        <p style="color:gray; margin-top:-6px;">
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
    if not token:
        st.error("No JWT token in session; cannot fetch transactions.")
        return

    # current stored values (may be Response objects or lists)
    transactions = st.session_state.get("transactions", [])
    categories = st.session_state.get("categories", [])

    # normalize to lists if already lists, else keep as-is for debugging
    if not isinstance(transactions, list):
        transactions = []

    if not isinstance(categories, list):
        categories = []

    # If no transactions, try to re-fetch
    if not transactions:
        # update to your import path

        refreshed = get_transactions(token)

        # DEBUG: print type and repr so you see exactly what's returned
        print("DEBUG refreshed type:", type(refreshed))
        try:
            print("DEBUG refreshed repr:", repr(refreshed)[:2000])  # avoid huge prints
        except Exception as e:
            print("DEBUG repr error:", e)

        # Handle common return shapes:
        # 1) requests.Response object
        if hasattr(refreshed, "status_code"):
            print("DEBUG response.status_code:", refreshed.status_code)
            try:
                body = refreshed.json()
                print("DEBUG response.json() type:", type(body))
            except Exception as e:
                body = None
                print("DEBUG response.json() failed:", e)

            if refreshed.status_code == 200 and isinstance(body, list) and len(body) > 0:
                transactions = body
                st.session_state["transactions"] = body
            elif refreshed.status_code == 200 and isinstance(body, dict):
                # maybe API returns {"transactions": [...]}
                if "transactions" in body and isinstance(body["transactions"], list):
                    transactions = body["transactions"]
                    st.session_state["transactions"] = transactions
                else:
                    print("DEBUG response 200 but unexpected body keys:", list(body.keys()))
            else:
                st.warning(f"API returned status {refreshed.status_code}. See console for details.")
                print("DEBUG response.text:", getattr(refreshed, "text", None))

        # 2) direct list from wrapper
        elif isinstance(refreshed, list):
            if len(refreshed) > 0:
                transactions = refreshed
                st.session_state["transactions"] = refreshed
            else:
                print("DEBUG refreshed list is empty")

        # 3) dict shaped return
        elif isinstance(refreshed, dict):
            if "transactions" in refreshed and isinstance(refreshed["transactions"], list) and refreshed["transactions"]:
                transactions = refreshed["transactions"]
                st.session_state["transactions"] = transactions
            else:
                print("DEBUG refreshed dict keys:", list(refreshed.keys()))

        else:
            print("DEBUG refreshed is None or unknown type")

        # Final fallback
        if not transactions:
            st.warning("No transactions found after re-fetch. Check backend/API, token, and server logs.")
            render_predictions_section_new(token)
            return

    # ---------------------------
    # Attach category names
    # ---------------------------
    cat_map = {c["id"]: c["name"] for c in categories}
    transactions_all = []
    for tx in transactions:
        tx["category_name"] = cat_map.get(tx.get("category_id"), "Uncategorized")
        transactions_all.append(tx)

    df_all = pd.DataFrame(transactions_all)
    
    # ======================================================
    # FILTER BAR UI
    # =====================================================    
    st.markdown(
    """
    <div style="
        padding:18px; 
        border-radius:12px; 
        background: #fafafa; 
        border:1px solid #e6e6e6;
        margin-bottom:25px;
    ">
        <h3 style="margin-top:0;">🔍 Filters</h3>
    </div>
    """,
    unsafe_allow_html=True
    )


    with st.container():
        # Ensure we have valid dates before calculating min/max
        df_valid_dates = preprocess_df(df_all.copy())
        
        if df_valid_dates.empty or df_valid_dates["transaction_date"].isnull().all():
            min_date_data = date.today() - timedelta(days=365)
            max_date_data = date.today()
        else:
            min_date_data = df_valid_dates["transaction_date"].min().date()
            max_date_data = df_valid_dates["transaction_date"].max().date()
        
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
    # RUN ANALYTICS
    # ======================================================
    
    # 1. Compute Filtered Data (Summary, Distribution, Table)
    filtered_results = compute_filtered_data(
        transactions_all,
        start_date=start_date,
        end_date=end_date,
        category=selected_category,
        tx_type=tx_type,
    )
    summary = filtered_results["summary"]
    expense_dist = filtered_results["expense_dist"]
    filtered = filtered_results["filtered"]
    
    # 2. Compute Unfiltered Monthly Trend (Independent of filters)
    monthly = compute_monthly_trend(transactions_all)


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
                <div style="font-size:26px; font-weight:600; color:{color};">Rp{value:,.2f}</div>
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
    # EXPENSE DETAIL LAYOUT (Pie Chart and Table Side-by-Side)
    # ======================================================
    
    st.markdown("""
    <div style="padding:18px; border-radius:12px; background:#fafafa; 
                  border:1px solid #eee; margin-bottom:25px;">
        <h3 style="margin-top:0;">📊 Detailed Breakdown </h3>
    </div>
    """, unsafe_allow_html=True)
    col_pie, col_table = st.columns(2)

    # --- PIE CHART (Expense Distribution) ---
    with col_pie:
        st.subheader("🥧 Expense Distribution")

        if expense_dist:
            df_exp = pd.DataFrame(expense_dist)
            df_exp['amount'] = pd.to_numeric(df_exp['amount'], errors='coerce')

            fig_pie = px.pie(
                df_exp,
                names="category_name",
                values="amount",
                hole=0.45
            )

            fig_pie.update_traces(
                textfont_size=20,      # font inside the pie
                hovertemplate='%{label}: %{value}<extra></extra>'
            )

            fig_pie.update_layout(
                legend=dict(font=dict(size=20)),   # legend size
                margin=dict(t=10, b=0, l=0, r=350)
            )

            st.plotly_chart(fig_pie, config={"responsive": True})

        else:
            st.info("No expense data found in the selected range.")

    # --- DETAILED EXPENSE TABLE (Filtered and Simplified) ---
    with col_table:
        st.subheader("📄 Expenses Table")
        
        if filtered:
            df_filtered = pd.DataFrame(filtered)
            
            # Filter for expense only
            df_expenses = df_filtered[df_filtered['type'].str.lower() == 'expense'].copy()
            
            if not df_expenses.empty:
                # Select, rename, and format columns
                df_expenses['Price'] = df_expenses['amount'].apply(format_currency)
                
                # Ensure transaction_date exists and use it
                df_expenses['Date'] = df_expenses['transaction_date'].dt.date
                
                df_display_table = df_expenses[[
                    'category_name', 
                    'Price', 
                    'Date'
                ]].rename(columns={
                    'category_name': 'Category'
                })
        
            
            if filtered:
                df_filtered = pd.DataFrame(filtered)
                
                # Filter for expense only
                df_expenses = df_filtered[df_filtered['type'].str.lower() == 'expense'].copy()
                
                if not df_expenses.empty:
                    
                    # 1. Select, rename, and format columns
                    df_expenses['Price'] = df_expenses['amount'].apply(format_currency)
                    
                    # 2. Extract Date
                    df_expenses['Date'] = df_expenses['transaction_date'].dt.date
                    
                    df_display_table = df_expenses[[
                        'category_name', 
                        'Price', 
                        'Date'
                    ]].rename(columns={
                        'category_name': 'Category'
                    })
                    
                    # 3. Filter out rows where any of the displayed columns are empty/null
                    # Note: Price is always a formatted string, so checking for NaN on original data or Date is enough.
                    df_display_table = df_display_table.dropna(subset=['Category', 'Date'])
                    
                    if not df_display_table.empty:
                        # Display the table with larger font via injected CSS
                        
                        st.dataframe(df_display_table, hide_index=True,use_container_width=True, height="auto")
                    else:
                        st.info("No expense transactions found with complete data after filtering.")
                else:
                    st.info("No expense transactions found matching the current filters.")
            else:
                st.info("No transactions match the current filters.")

    st.markdown("<br>", unsafe_allow_html=True) # Add space after the charts


    # ======================================================
    # MONTHLY TREND CHART (Full Width)
    # ======================================================
    st.markdown("""
        <div style="padding:18px; border-radius:12px; background:#fafafa; 
                    border:1px solid #eee; margin-bottom:25px;">
            <h3 style="margin-top:0;">📈 Monthly Income vs Expense </h3>
        </div>
        """, unsafe_allow_html=True)


    if monthly:
        df_month = pd.DataFrame(monthly)
        df_month["income"] = pd.to_numeric(df_month.get("income", 0), errors='coerce')
        df_month["expense"] = pd.to_numeric(df_month.get("expense", 0), errors='coerce')

        fig_line = px.line(df_month, x="month", y=["income", "expense"], markers=True, color_discrete_map={
            "income": "green",
            "expense": "red"})
        fig_line.update_xaxes(type='category') 
        fig_line.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No monthly data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # AI PREDICTIONS
    # ======================================================
    render_predictions_section_new(token)