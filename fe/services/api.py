import requests
import streamlit as st
from typing import Optional


API_URL = "http://127.0.0.1:5000"

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.jwt}"}

def auth_header(token): 
    return {"Authorization": f"Bearer {token}"} 

# ========== LOGIN / USER HANDLER ==========
def login(email, password):
    url = f"{API_URL}/users/login"
    response = requests.post(url, json={"email": email, "password": password})
    return response

def register(email, password, first_name, last_name): 
    url = f'{API_URL}/users'
    data = {
        "email": email, 
        "password": password, 
        "first_name": first_name,
        "last_name": last_name
    }
    response = requests.post(url, json=data)
    return response

def get_user(user_id, token):
    url = f"{API_URL}/users/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def update_user(user_id, token, email=None, first_name=None, last_name=None, password=None):
    url = f"{API_URL}/users/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}

    data = {}
    if email: data["email"] = email
    if first_name: data["first_name"] = first_name
    if last_name: data["last_name"] = last_name
    if password: data["password"] = password

    return requests.put(url, json=data, headers=headers)

# ADMIN ONLY
def delete_user(user_id, token):
    url = f"{API_URL}/users/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# ========== TRANSACT DATA ==========
def get_transactions(token):
    url = f"{API_URL}/transactions"
    return requests.get(url, headers=auth_header(token))

def create_transaction(token, user_id, category_id, amount, description, tx_type, tx_date):
    """
    tx_type = "income" or "expense"
    tx_date must be "DD-MM-YYYY"
    """
    url = f"{API_URL}/transactions"
    data = {
        "user_id": user_id,
        "category_id": category_id,
        "amount": amount,
        "description": description,
        "type": tx_type,
        "transaction_date": tx_date
    }
    return requests.post(url, json=data, headers=auth_header(token))

def delete_transaction(tx_id, token):
    url = f"{API_URL}/transactions/{tx_id}"
    return requests.delete(url, headers=auth_header(token))

def update_transaction(tx_id, data, token):
    """
    data can be any of these:
    {
        "category_id": ...,
        "amount": ...,
        "description": ...,
        "type": "income"/"expense",
        "transaction_date": "DD-MM-YYYY"
    }
    """
    url = f"{API_URL}/transactions/{tx_id}"
    return requests.put(url, json=data, headers=auth_header(token))

def group_transactions_by_type(token):
    url = f"{API_URL}/transactions/group/type"
    return requests.get(url, headers=auth_header(token))

def group_transactions_by_type_category(token):
    url = f"{API_URL}/transactions/group/type-category"
    return requests.get(url, headers=auth_header(token))

def predict_by_type(token, tx_type):
    """
    tx_type: "income" or "expense"
    """
    url = f"{API_URL}/transactions/predict/type"
    params = {"type": tx_type}
    return requests.get(url, params=params, headers=auth_header(token))

def predict_by_type_category(token, category_id):
    url = f"{API_URL}/transactions/predict/type-category"
    params = {"category_id": category_id}
    return requests.get(url, params=params, headers=auth_header(token))

# ========== CATEGORY ==========
def get_categories(token: str):
    """GET /categories. Returns the Response object."""
    url = f"{API_URL}/categories"
    try:
        return requests.get(url, headers=auth_header(token))
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching categories: {e}")
        return None

def create_category(token: str, name: str, type_value: str, user_id: int = None):
    """
    POST /categories  
    type_value: "income" or "expense" (lowercase)
    If user is not admin, backend ignores provided user_id and uses JWT identity.
    """
    url = f"{API_URL}/categories"
    payload = {"name": name, "type": type_value}
    if user_id is not None:
        payload["user_id"] = user_id

    return requests.post(url, json=payload, headers={**auth_header(token)})

def update_category(token: str, category_id: int, data: dict):
    """
    PUT /categories/<id>
    data can contain:
    { "name": "...", "type": "income"/"expense" }
    """
    url = f"{API_URL}/categories/{category_id}"
    return requests.put(url, json=data, headers=auth_header(token))

def delete_category(token: str, category_id: int):
    """DELETE /categories/<id>"""
    url = f"{API_URL}/categories/{category_id}"
    return requests.delete(url, headers=auth_header(token))

# ========== BUDGET ==========
def get_budgets(token: str) -> requests.Response:
    """
    GET /budgets
    Retrieves all budgets for the current user (or all budgets if admin).
    """
    url = f"{API_URL}/budgets"
    return requests.get(url, headers=auth_header(token))

def create_budget(
    token: str,
    category_id: int,
    budget_amount: float,
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None
) -> requests.Response:
    """
    POST /budgets
    start_date and end_date should be formatted as "DD-MM-YYYY".
    If user is not admin, the backend ignores a provided user_id and uses JWT identity.
    """
    url = f"{API_URL}/budgets"
    payload = {
        "category_id": category_id,
        "budget_amount": budget_amount,
        "start_date": start_date,
        "end_date": end_date,
    }
    
    # Allow passing user_id, which the backend will use only if the user is an admin.
    if user_id is not None:
        payload["user_id"] = user_id

    return requests.post(url, json=payload, headers=auth_header(token))

def update_budget(
    token: str,
    budget_id: int,
    data: dict[str, any]
) -> requests.Response:
    """
    PUT /budgets/<id>
    data can contain:
    { 
        "budget_amount": float, 
        "start_date": "DD-MM-YYYY", 
        "end_date": "DD-MM-YYYY" 
    }
    """
    url = f"{API_URL}/budgets/{budget_id}"
    return requests.put(url, json=data, headers=auth_header(token))

def delete_budget(token: str, budget_id: int) -> requests.Response:
    """
    DELETE /budgets/<id>
    """
    url = f"{API_URL}/budgets/{budget_id}"
    return requests.delete(url, headers=auth_header(token))
