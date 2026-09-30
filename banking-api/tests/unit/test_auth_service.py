# tests/unit/test_auth_service.py
# Unit tests for login (AuthService). The user and session repositories are
# replaced with Mocks, so these tests don't need any database.
from unittest.mock import Mock

import pytest

from errors import AuthError
from models.user import User
from repository.session_repository import SessionRepository
from repository.user_repository import UserRepository
from services.auth_service import AuthService, hash_password

SALT = "00112233445566778899aabbccddeeff"
JOHN = User(id=1, username="john", full_name="John Doe", role="CUSTOMER", customer_id=1,
            salt=SALT, password_hash=hash_password("password123", SALT))


@pytest.fixture
def sessions():
    return Mock(spec=SessionRepository)


@pytest.fixture
def auth_service(sessions):
    users = Mock(spec=UserRepository)
    users.find_by_username.side_effect = lambda name: JOHN if name == "john" else None
    users.get.side_effect = lambda user_id: JOHN if user_id == 1 else None
    return AuthService(users, sessions)


def test_correct_password_logs_in_and_creates_session(auth_service, sessions):
    result = auth_service.login("  John ", "password123")  # spaces + capitals ignored

    assert result["user"].username == "john"
    assert "password_hash" not in result["user"].model_dump()  # never sent to the browser
    sessions.create.assert_called_once_with(result["token"], 1)


@pytest.mark.parametrize("username,password", [("john", "wrong"), ("nobody", "password123")])
def test_bad_login_is_rejected(auth_service, sessions, username, password):
    with pytest.raises(AuthError, match="Incorrect username or password"):
        auth_service.login(username, password)

    sessions.create.assert_not_called()


def test_valid_token_returns_the_user(auth_service, sessions):
    sessions.get_user_id.return_value = 1

    assert auth_service.current_user("some-token").username == "john"


def test_no_token_means_not_logged_in(auth_service):
    with pytest.raises(AuthError):
        auth_service.current_user(None)


def test_expired_token_means_not_logged_in(auth_service, sessions):
    sessions.get_user_id.return_value = None  # session was deleted / expired

    with pytest.raises(AuthError):
        auth_service.current_user("old-token")


def test_logout_deletes_the_session(auth_service, sessions):
    auth_service.logout("some-token")

    sessions.delete.assert_called_once_with("some-token")