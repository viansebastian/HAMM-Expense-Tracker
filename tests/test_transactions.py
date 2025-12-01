import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from datetime import datetime
from flask_jwt_extended import JWTManager 

from be.controllers.transact_controller import transact_bp
from be import models 

# --- FIXTURES ---

@pytest.fixture(autouse=True)
def mock_jwt_verify():
    """Bypasses JWT verification logic."""
    with patch("flask_jwt_extended.view_decorators.verify_jwt_in_request") as mock:
        yield mock

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(transact_bp)
    app.config["TESTING"] = True
    return app.test_client()

@pytest.fixture
def mock_db_session():
    with patch("be.controllers.transact_controller.SessionLocal") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_jwt():
    with patch("be.controllers.transact_controller.get_jwt_identity", return_value="1") as mock:
        yield mock

@pytest.fixture
def mock_check_exists():
    # FIX #1: Patch WHERE it is imported (in the controller), not where it is defined
    with patch("be.controllers.transact_controller.check_exists", return_value=False) as mock:
        yield mock

# --- TESTS ---

def test_get_transactions_success(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"
    
    mock_tx = MagicMock()
    mock_tx.id = 10
    mock_tx.user_id = 1
    mock_tx.amount = 50000.0
    mock_tx.category_id = 2
    mock_tx.description = "Lunch"
    mock_tx.type.value = "expense"
    mock_tx.transaction_date = datetime(2023, 10, 5)
    mock_tx.created_at = datetime.now()
    mock_tx.updated_at = datetime.now()

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_tx]

    response = client.get("/transactions")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["amount"] == 50000.0

def test_create_transaction_success(client, mock_db_session, mock_jwt, mock_check_exists):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"
    
    mock_category = MagicMock()
    mock_category.id = 5
    mock_category.user_id = 1
    mock_category.type.value = "expense"
    mock_category.name = "Food"

    # The controller calls .first() twice: once for user, once for category
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_category]

    payload = {
        "category_id": 5,
        "amount": 10000,
        "description": "Burger",
        "type": "expense",
        "transaction_date": "25-10-2023"
    }

    response = client.post("/transactions", json=payload)

    # This should now pass 201 because check_exists is correctly patched to return False
    assert response.status_code == 201
    assert "New Transaction added" in response.get_json()["message"]

def test_create_transaction_type_mismatch(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"
    
    mock_category = MagicMock()
    mock_category.id = 5
    mock_category.user_id = 1  # FIX #2: Must belong to user 1, or we get 403 Forbidden
    mock_category.type.value = "expense" 

    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_category]

    payload = {
        "category_id": 5,
        "amount": 10000,
        "type": "income", # Mismatch!
        "transaction_date": "25-10-2023"
    }

    response = client.post("/transactions", json=payload)

    assert response.status_code == 400
    assert "Category type mismatch" in response.get_json()["error"]

def test_predict_linear_regression_logic(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    t1 = MagicMock(amount=100, transaction_date=datetime(2023, 1, 1))
    t2 = MagicMock(amount=120, transaction_date=datetime(2023, 2, 1))
    t3 = MagicMock(amount=140, transaction_date=datetime(2023, 3, 1))
    
    mock_db_session.query.return_value.filter.return_value.all.return_value = [t1, t2, t3]

    response = client.get("/transactions/predict/type?type=expense")

    assert response.status_code == 200
    data = response.get_json()
    predictions = data["predicted_next_months"]
    
    assert len(predictions) == 2
    # FIX #3: Predictions is a flat list [160.0, 180.0], not [[160.0], [180.0]]
    assert 159 < predictions[0] < 161 

def test_predict_not_enough_data(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    t1 = MagicMock(amount=100, transaction_date=datetime(2023, 1, 1))
    mock_db_session.query.return_value.filter.return_value.all.return_value = [t1]

    response = client.get("/transactions/predict/type?type=expense")

    assert response.status_code == 400
    assert "Not enough data" in response.get_json()["error"]