# tests/unit/test_auth_service.py
# Unit tests for login (AuthService) and the JWT helpers in security.py.
# The user repository is a Mock, so these tests don't need any database.
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import jwt
import pytest

from config import JWT_ALGORITHM, JWT_SECRET
from errors import AuthError, RateLimitError
from models.user import User
from repository.user_repository import UserRepository
from security import LoginRateLimiter, decode_access_token
from services.auth_service import AuthService, hash_password

SALT = "00112233445566778899aabbccddeeff"
JOHN = User(id=1, username="john", full_name="John Doe", role="CUSTOMER", customer_id=1,
            salt=SALT, password_hash=hash_password("password123", SALT))


@pytest.fixture
def auth_service():
    users = Mock(spec=UserRepository)
    users.find_by_username.side_effect = lambda name: JOHN if name == "john" else None
    return AuthService(users, LoginRateLimiter(max_failures=3, window_seconds=60))


# ---------- Login ----------

def test_correct_password_returns_a_jwt(auth_service):
    result = auth_service.login("  John ", "password123")  # spaces + capitals ignored

    assert result["user"].username == "john"
    assert "password_hash" not in result["user"].model_dump()  # never sent to the browser
    assert result["token"].count(".") == 2                      # a JWT has 3 parts


def test_jwt_holds_username_role_and_expiry(auth_service):
    token = auth_service.login("john", "password123")["token"]

    claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert claims["sub"] == "john"
    assert claims["role"] == "CUSTOMER"
    assert claims["exp"] > claims["iat"]                        # it expires


@pytest.mark.parametrize("username,password", [("john", "wrong"), ("nobody", "password123")])
def test_bad_login_is_rejected(auth_service, username, password):
    with pytest.raises(AuthError, match="Incorrect username or password"):
        auth_service.login(username, password)


# ---------- Token validation ----------

def test_valid_token_returns_the_user(auth_service):
    token = auth_service.login("john", "password123")["token"]

    assert auth_service.current_user(token).customer_id == 1


def test_no_token_means_not_logged_in(auth_service):
    with pytest.raises(AuthError):
        auth_service.current_user(None)


def test_expired_token_is_rejected():
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    token = jwt.encode({"sub": "john", "uid": 1, "role": "CUSTOMER", "name": "John Doe",
                        "iat": past, "exp": past + timedelta(minutes=60)},
                       JWT_SECRET, algorithm=JWT_ALGORITHM)

    with pytest.raises(AuthError, match="expired"):
        decode_access_token(token)


def test_token_signed_with_another_secret_is_rejected():
    # Someone makes their own token claiming to be an ADMIN, but doesn't know our secret.
    fake = jwt.encode({"sub": "hacker", "uid": 99, "role": "ADMIN", "name": "Hacker",
                       "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                      "not-our-secret", algorithm=JWT_ALGORITHM)

    with pytest.raises(AuthError, match="Invalid"):
        decode_access_token(fake)


def test_edited_token_is_rejected(auth_service):
    token = auth_service.login("john", "password123")["token"]
    header, payload, signature = token.split(".")

    with pytest.raises(AuthError):
        decode_access_token(header + "." + payload + "x." + signature)


# ---------- Rate limiting ----------

def test_too_many_wrong_passwords_blocks_the_username(auth_service):
    for _ in range(3):
        with pytest.raises(AuthError):
            auth_service.login("john", "wrong")

    # Even the RIGHT password is refused now, until the block wears off.
    with pytest.raises(RateLimitError):
        auth_service.login("john", "password123")


def test_block_wears_off_after_the_window():
    now = [1000.0]
    limiter = LoginRateLimiter(max_failures=2, window_seconds=60, clock=lambda: now[0])
    limiter.record_failure("john")
    limiter.record_failure("john")
    with pytest.raises(RateLimitError):
        limiter.check("john")

    now[0] += 61                                                 # a minute later

    limiter.check("john")                                        # allowed again


def test_successful_login_resets_the_count(auth_service):
    for _ in range(2):
        with pytest.raises(AuthError):
            auth_service.login("john", "wrong")
    auth_service.login("john", "password123")                    # resets

    for _ in range(2):                                           # 2 more are fine
        with pytest.raises(AuthError):
            auth_service.login("john", "wrong")
    auth_service.login("john", "password123")
