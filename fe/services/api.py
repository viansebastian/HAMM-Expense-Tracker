import requests
import streamlit as st


API_URL = "http://127.0.0.1:5000"

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.jwt}"}

# ========== LOGIN ==========
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

# ========== GET ALL DATA ==========
def get_categories():
    return requests.get(f"{API_URL}/categories", headers=auth_headers()).json()

def get_budgets():
    return requests.get(f"{API_URL}/budgets", headers=auth_headers()).json()

def get_transactions():
    return requests.get(f"{API_URL}/transactions", headers=auth_headers()).json()

# ========== POST DATA ==========
def create_transaction(data):
    return requests.post(f"{API_URL}/transactions", json=data, headers=auth_headers())

def create_category(data):
    return requests.post(f"{API_URL}/categories", json=data, headers=auth_headers())

def create_budget(data):
    return requests.post(f"{API_URL}/budgets", json=data, headers=auth_headers())
