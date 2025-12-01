import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from datetime import datetime
from flask_jwt_extended import JWTManager 

from be.controllers.category_controller import category_bp
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
    JWTManager(app) # Initialize JWT Manager
    app.register_blueprint(category_bp)
    app.config["TESTING"] = True
    return app.test_client()

@pytest.fixture
def mock_db_session():
    # Make sure this matches your file structure
    with patch("be.controllers.category_controller.SessionLocal") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_jwt():
    # Mocking the User ID returned by get_jwt_identity
    with patch("be.controllers.category_controller.get_jwt_identity", return_value="1") as mock:
        yield mock

@pytest.fixture
def mock_check_exists():
    # CRITICAL: Patch where it is IMPORTED (in the controller), not where defined
    with patch("be.controllers.category_controller.check_exists", return_value=False) as mock:
        yield mock

# --- TESTS ---

def test_get_categories_success(client, mock_db_session, mock_jwt):
    # 1. Mock User
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    # 2. Mock Category Data
    mock_cat = MagicMock()
    mock_cat.id = 10
    mock_cat.user_id = 1
    mock_cat.name = "Groceries"
    mock_cat.type.value = "expense" # Mocking Enum
    mock_cat.created_at = datetime.now()
    mock_cat.updated_at = datetime.now()

    # 3. Setup DB Returns
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_cat]

    # 4. Request
    response = client.get("/categories")

    # 5. Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Groceries"
    assert data[0]["type"] == "expense"

def test_create_category_success(client, mock_db_session, mock_jwt, mock_check_exists):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    # Mock user query
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    payload = {
        "name": "Salary",
        "type": "income"
    }

    response = client.post("/categories", json=payload)

    assert response.status_code == 201
    assert "Category created successfully" in response.get_json()["message"]
    
    # Verify DB interactions
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

def test_create_category_already_exists(client, mock_db_session, mock_jwt):
    """Test that it returns 400 if check_exists returns True."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    # Manually patch check_exists just for this test to return True
    with patch("be.controllers.category_controller.check_exists", return_value=True):
        payload = {
            "name": "Salary",
            "type": "income"
        }
        response = client.post("/categories", json=payload)

    assert response.status_code == 400
    assert "already exists" in response.get_json()["error"]

def test_update_category_success(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    mock_cat = MagicMock()
    mock_cat.id = 5
    mock_cat.user_id = 1 # Important: Must match user_id
    mock_cat.name = "Old Name"
    mock_cat.type.value = "expense"

    # side_effect: 1st call for User, 2nd call for Category
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_cat]

    payload = {"name": "New Name"}

    response = client.put("/categories/5", json=payload)

    assert response.status_code == 200
    assert "updated successfully" in response.get_json()["message"]
    # Verify the object was actually updated in memory
    assert mock_cat.name == "New Name"
    mock_db_session.commit.assert_called_once()

def test_update_category_not_found_or_forbidden(client, mock_db_session, mock_jwt):
    """Test trying to update a category that doesn't belong to the user."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    # First call returns User, Second call (Category) returns None (not found or filtered out)
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, None]

    payload = {"name": "Hacker Edit"}

    response = client.put("/categories/99", json=payload)

    assert response.status_code == 404
    assert "Category not found" in response.get_json()["error"]

def test_delete_category_success(client, mock_db_session, mock_jwt):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"

    mock_cat = MagicMock()
    mock_cat.id = 5
    mock_cat.user_id = 1

    # side_effect: 1st call User, 2nd call Category
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_cat]

    response = client.delete("/categories/5", json={})

    assert response.status_code == 200
    assert "deleted successfully" in response.get_json()["message"]
    mock_db_session.delete.assert_called_once_with(mock_cat)
    mock_db_session.commit.assert_called_once()