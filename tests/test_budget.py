import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from datetime import datetime
from flask_jwt_extended import JWTManager

# IMPORTS: Update if your controller file is named differently
from be.controllers.budget_controller import budget_bp
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
    app.register_blueprint(budget_bp)
    app.config["TESTING"] = True
    return app.test_client()

@pytest.fixture
def mock_db_session():
    with patch("be.controllers.budget_controller.SessionLocal") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_jwt():
    with patch("be.controllers.budget_controller.get_jwt_identity", return_value="1") as mock:
        yield mock

@pytest.fixture
def mock_check_exists():
    # Patch check_exists in the budget controller
    with patch("be.controllers.budget_controller.check_exists", return_value=False) as mock:
        yield mock

# --- TESTS ---

def test_get_budgets_success(client, mock_db_session, mock_jwt):
    # 1. Mock User
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    # 2. Mock Budget Data
    mock_budget = MagicMock()
    mock_budget.id = 1
    mock_budget.user_id = 1
    mock_budget.category_id = 5
    mock_budget.budget_amount = 500000.0
    mock_budget.start_date = datetime(2023, 10, 1)
    mock_budget.end_date = datetime(2023, 10, 31)
    mock_budget.created_at = datetime.now()
    mock_budget.updated_at = datetime.now()

    # 3. Setup DB Returns
    # First query gets User, second query gets Budgets
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_budget]

    # 4. Request
    response = client.get("/budgets")

    # 5. Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["budget_amount"] == 500000.0
    assert "start_date" in data[0]


def test_create_budget_success(client, mock_db_session, mock_jwt, mock_check_exists):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    payload = {
        "category_id": 5,
        "budget_amount": 1000000,
        "start_date": "01-11-2023",
        "end_date": "30-11-2023"
    }

    response = client.post("/budgets", json=payload)

    assert response.status_code == 201
    assert "Budget created successfully" in response.get_json()["message"]
    
    # Verify DB interactions
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_create_budget_duplicate(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    # Force check_exists to return True
    with patch("be.controllers.budget_controller.check_exists", return_value=True):
        payload = {
            "category_id": 5,
            "budget_amount": 1000000,
            "start_date": "01-11-2023",
            "end_date": "30-11-2023"
        }
        response = client.post("/budgets", json=payload)

    assert response.status_code == 400
    assert "budget already exists" in response.get_json()["error"]


def test_update_budget_success(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    mock_budget = MagicMock()
    mock_budget.id = 10
    mock_budget.user_id = 1
    
    # FIX: Added category_id to prevent MagicMock serialization error
    mock_budget.category_id = 5 
    
    mock_budget.budget_amount = 50000.0
    mock_budget.start_date = datetime(2023, 10, 1)
    mock_budget.end_date = datetime(2023, 10, 31)

    # side_effect: 1st call = User, 2nd call = Budget
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_budget]

    payload = {
        "budget_amount": 75000.0
    }

    response = client.put("/budgets/10", json=payload)

    assert response.status_code == 200
    assert "updated successfully" in response.get_json()["message"]
    assert mock_budget.budget_amount == 75000.0
    mock_db_session.commit.assert_called_once()


def test_update_budget_not_found(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    # User found, Budget NOT found (None)
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, None]

    payload = {"budget_amount": 75000.0}

    response = client.put("/budgets/999", json=payload)

    assert response.status_code == 404
    assert "Budget not found" in response.get_json()["error"]


def test_delete_budget_success(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    mock_budget = MagicMock()
    mock_budget.id = 10
    mock_budget.user_id = 1

    # side_effect: 1st call = User, 2nd call = Budget
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_budget]

    response = client.delete("/budgets/10")

    assert response.status_code == 200
    assert "deleted successfully" in response.get_json()["message"]
    mock_db_session.delete.assert_called_once_with(mock_budget)
    mock_db_session.commit.assert_called_once()