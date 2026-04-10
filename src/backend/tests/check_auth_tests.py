import pytest
from unittest.mock import MagicMock, patch

from app import check_auth 

## 1. Success Cases
@patch('app.db')
def test_check_auth_valid_headers(mock_db):
    """Test that auth passes when both User-ID and Authorization are provided."""
    mock_db.get_user_token.return_value = "Bearer some_token"

    headers = {
        "User-ID": "123",
        "Authorization": "Bearer some_token"
    }
    assert check_auth(headers) is True

## 2. Missing Header Cases
@pytest.mark.parametrize("headers", [
    ({"User-ID": "123"}),                 # Missing Authorization
    ({"Authorization": "Bearer token"}),  # Missing User-ID
    ({}),                                 # Empty dict
])
def test_check_auth_missing_headers(headers):
    """Test that auth fails if either required header is missing."""
    assert check_auth(headers) is False

## 3. Testing with Mocked Database
@patch('app.db')
def test_check_auth_token_matching(mock_db):
    """
    This test assumes you change 'check = True' in your function.
    It verifies that the token from the header matches the DB token.
    """
    # Setup the mock database response
    mock_db.get_user_token.return_value = "Bearer valid_token"
    
    test_headers = {
        "User-ID": "user1",
        "Authorization": "Bearer valid_token"
    }
    
    assert check_auth(test_headers) is True

@patch('app.db')
def test_check_auth_malformed_bearer(mock_db):
    """Tests that the function handles 'split()[-1]' correctly."""
    mock_db.get_user_token.return_value = "token_without_bearer"

    test_headers = {
        "User-ID": "123",
        "Authorization": "token_without_bearer" # split()[-1] will just be the token
    }
    assert check_auth(test_headers) is True