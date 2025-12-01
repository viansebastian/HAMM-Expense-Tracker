import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from flask_jwt_extended import JWTManager

# IMPORTS: Update if your controller file is named differently
from be.controllers.user_controller import user_bp
from be import models 

# --- FIXTURES ---

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app) # Initialize JWT Manager for create_access_token
    app.register_blueprint(user_bp)
    app.config["TESTING"] = True
    return app.test_client()

@pytest.fixture
def mock_db_session():
    with patch("be.controllers.user_controller.SessionLocal") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_check_exists():
    # Patching check_exists where it is used in the controller
    with patch("be.controllers.user_controller.check_exists", return_value=False) as mock:
        yield mock

# --- TESTS ---

def test_get_users_success(client, mock_db_session):
    # 1. Mock Data
    mock_u1 = MagicMock()
    mock_u1.id = 1
    mock_u1.email = "test@example.com"
    mock_u1.first_name = "John"
    mock_u1.last_name = "Doe"

    # 2. Setup DB Return
    mock_db_session.query.return_value.all.return_value = [mock_u1]

    # 3. Request
    response = client.get("/users")

    # 4. Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"
    assert data[0]["first_name"] == "John"


def test_create_user_success(client, mock_db_session, mock_check_exists):
    payload = {
        "email": "new@example.com",
        "password": "password123",
        "first_name": "Jane",
        "last_name": "Doe"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 201
    assert "User created successfully" in response.get_json()["message"]
    
    # Verify DB interactions
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_create_user_already_exists(client, mock_db_session):
    # Force check_exists to return True
    with patch("be.controllers.user_controller.check_exists", return_value=True):
        payload = {
            "email": "existing@example.com",
            "password": "password123"
        }
        response = client.post("/users", json=payload)

    assert response.status_code == 200 # Note: Your code returns 200 with error key, not 400 or 409
    assert "User with this email already exists" in response.get_json()["error"]
    mock_db_session.add.assert_not_called()


def test_update_user_success(client, mock_db_session):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "old@example.com"
    # FIX: Define these to prevent MagicMock from creating nested mocks that crash jsonify
    mock_user.first_name = "OldName"
    mock_user.last_name = "OldLast"

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    payload = {"email": "updated@example.com"}

    response = client.put("/users/1", json=payload)

    assert response.status_code == 200
    assert "updated successfully" in response.get_json()["message"]
    assert mock_user.email == "updated@example.com"
    mock_db_session.commit.assert_called_once()


def test_delete_user_success(client, mock_db_session):
    mock_user = MagicMock()
    mock_user.id = 1

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.delete("/users/1")

    assert response.status_code == 200
    assert "deleted successfully" in response.get_json()["message"]
    mock_db_session.delete.assert_called_once_with(mock_user)
    mock_db_session.commit.assert_called_once()


def test_login_success(client, mock_db_session):
    """
    Tests login based on current controller logic: `user.password_hash == password`.
    """
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.role = "user"
    # Logic matches Plain text to "Hash", so we set hash to plain text for test to pass
    mock_user.password_hash = "secret123" 

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    payload = {
        "email": "test@example.com",
        "password": "secret123"
    }

    response = client.post("/users/login", json=payload)

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["message"] == "Login successful"


def test_login_failure_wrong_password(client, mock_db_session):
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.password_hash = "real_password"

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    payload = {
        "email": "test@example.com",
        "password": "wrong_password"
    }

    response = client.post("/users/login", json=payload)

    assert response.status_code == 401
    assert "Invalid email or password" in response.get_json()["error"]