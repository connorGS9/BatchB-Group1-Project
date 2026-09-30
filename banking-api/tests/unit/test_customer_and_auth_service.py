# tests/unit/test_customer_and_auth_service.py
# Unit tests for customer rules and login, with the repositories mocked (see conftest.py).
from unittest.mock import Mock

import pytest

from errors import AuthError, NotFoundError, ValidationError
from models.customer import Customer, CustomerCreate, CustomerUpdate
from models.user import User
from repository.session_repository import SessionRepository
from repository.user_repository import UserRepository
from services.auth_service import AuthService, hash_password
from services.customer_service import CustomerService


def make_customer(**overrides):
    fields = dict(id=1, first_name="John", last_name="Doe", email="john.doe@example.com",
                  phone="555-0100", is_active=True)
    fields.update(overrides)
    return Customer(**fields)


# ---------- Customers ----------

@pytest.fixture
def customer_service(customer_repo):
    customer_repo.add.side_effect = lambda c: c.model_copy(update={"id": 6})
    customer_repo.update.side_effect = lambda c: c
    return CustomerService(customer_repo)


def test_duplicate_email_is_rejected(customer_service, customer_repo):
    customer_repo.find_by_email.return_value = make_customer()
    data = CustomerCreate(first_name="J", last_name="D", email="john.doe@example.com", phone="555")

    with pytest.raises(ValidationError, match="already in use"):
        customer_service.create_customer(data)

    customer_repo.add.assert_not_called()


def test_new_customer_is_created_active(customer_service, customer_repo):
    customer_repo.find_by_email.return_value = None
    data = CustomerCreate(first_name="New", last_name="Person", email="new@example.com", phone="555")

    customer = customer_service.create_customer(data)

    assert customer.id == 6
    assert customer.is_active is True


def test_update_only_changes_given_fields(customer_service, customer_repo):
    customer_repo.get.return_value = make_customer()

    updated = customer_service.update_customer(1, CustomerUpdate(phone="555-9999"))

    assert updated.phone == "555-9999"
    assert updated.first_name == "John"  # untouched


def test_update_missing_customer_is_not_found(customer_service, customer_repo):
    customer_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        customer_service.update_customer(99, CustomerUpdate(phone="1"))


# ---------- Login ----------

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


def test_no_token_means_not_logged_in(auth_service):
    with pytest.raises(AuthError):
        auth_service.current_user(None)
