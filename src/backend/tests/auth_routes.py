import pytest
import sys
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash

# --- PREVENT AI LOADING ---
mock_mods = ["chromadb", "chromadb.utils", "sentence_transformers"]
for mod in mock_mods:
    sys.modules[mod] = MagicMock()

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    with patch('app.db') as m_db:
        yield m_db

# --- TESTS ---

def test_signup_success(client, mock_db):
    """Tests signup and ensures User-ID is handled as a simple value"""
    mock_db.get_user_id.return_value = 101
    mock_db.check_for_username.return_value = False
    
    response = client.post('/signup', json={
        "username": "Anthony",
        "password": "password123"
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["User-ID"] == 101
    assert data["user_id"] == "Anthony"

def test_login_success(client, mock_db):
    """Tests login with matching hashed passwords"""
    password = "secure_pw"
    hashed = generate_password_hash(password)
    
    mock_db.get_user_login.return_value = {
        "User-ID": 101,
        "password": hashed
    }
    
    response = client.post('/login', json={
        "username": "Anthony",
        "password": password
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert "Authorization" in data
    assert data["User-ID"] == 101

def test_login_invalid_credentials(client, mock_db):
    """Tests that wrong password returns 401"""
    mock_db.get_login_data.return_value = {
        "User-ID": 101,
        "password": generate_password_hash("real_password")
    }
    
    response = client.post('/login', json={
        "username": "Anthony",
        "password": "wrong_password"
    })
    
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials"

def test_signup_duplicate_username(client, mock_db):
    """Test that signup fails if the username already exists in the DB"""
    mock_db.check_for_username.return_value = True  # Simulates finding a user

    # Try to sign up with that same username
    response = client.post('/signup', json={
        "username": "Anthony",
        "password": "newpassword123"
    })

    assert response.status_code == 409
    data = response.get_json()
    assert data["error"] == "Username already exists"
    
    assert not mock_db.insert.called