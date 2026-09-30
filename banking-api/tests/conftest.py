# tests/conftest.py
# Shared pytest fixtures. Unit tests run WITHOUT MongoDB: every repository is a
# Mock, so tests exercise only the service layer's business rules.
import os

# db.py reads MONGO_URL at import time. MongoClient connects lazily, so a dummy
# URL is enough as long as no test touches a real repository.
os.environ.setdefault("MONGO_URL", "mongodb://unused-in-unit-tests:27017")

from unittest.mock import Mock

import pytest

from models.account import Account
from repository.account_repository import AccountRepository
from repository.customer_repository import CustomerRepository
from repository.transaction_repository import TransactionRepository
from services.account_service import AccountService
from services.transaction_service import TransactionService


@pytest.fixture
def make_account():
    """Build an Account with sensible defaults; override any field per test."""
    def _make(**overrides) -> Account:
        fields = dict(id=1, account_number="ACC001", customer_id=1, first_name="John",
                      last_name="Doe", balance=1000.0, branch_id=1, is_active=True)
        fields.update(overrides)
        return Account(**fields)
    return _make


# --- Mocked repositories (spec= makes a typo'd method name fail loudly) ---

@pytest.fixture
def account_repo():
    return Mock(spec=AccountRepository)


@pytest.fixture
def customer_repo():
    return Mock(spec=CustomerRepository)


@pytest.fixture
def transaction_repo():
    return Mock(spec=TransactionRepository)


# --- Services wired to the mocks ---

@pytest.fixture
def account_service(account_repo, customer_repo):
    return AccountService(account_repo, customer_repo)


@pytest.fixture
def transaction_service(transaction_repo, account_service):
    return TransactionService(transaction_repo, account_service)
