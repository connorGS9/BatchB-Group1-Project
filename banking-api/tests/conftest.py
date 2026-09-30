# tests/conftest.py
# Shared pytest fixtures.
#
# These tests run WITHOUT a real MongoDB: we swap db.py's client for an in-memory
# mongomock client and seed it to mirror mongo-init/init-db.js. The same seeded
# database is shared three ways:
#   - injected explicitly into repositories        (repository tests)
#   - through the services built on those repos     (service tests)
#   - through the app's dependencies.py singletons  (API tests via TestClient)
# so a transfer made through the API is visible to a repository query in the
# same test. Each test gets a freshly reseeded database (see `fake_db`).
import os
from datetime import datetime, timezone

# db.py reads MONGO_URL at import time; a dummy is fine since we never connect.
os.environ.setdefault("MONGO_URL", "mongodb://unused-in-tests:27017")
os.environ.setdefault("MONGO_DB", "banking")
# config.py requires these secrets; tests use fixed fake values.
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-unit-tests-0123456789")
os.environ.setdefault("API_KEY", "test-api-key")

import mongomock
import pytest

# IMPORTANT: replace the client BEFORE importing any repository or the app, so
# every `database=db` default argument and every dependencies.py singleton binds
# to this in-memory database instead of a real Mongo.
import db as db_module

_client = mongomock.MongoClient()
db_module.client = _client
db_module.db = _client["banking"]

# Now it is safe to import things that capture db_module.db.
from models.account import Account  # noqa: E402
from repository.account_repository import AccountRepository  # noqa: E402
from repository.customer_repository import CustomerRepository  # noqa: E402
from repository.transaction_repository import TransactionRepository  # noqa: E402
from repository.branch_repository import BranchRepository  # noqa: E402
from services.account_service import AccountService  # noqa: E402
from services.customer_service import CustomerService  # noqa: E402
from services.transaction_service import TransactionService  # noqa: E402


# --------------------------------------------------------------------------
# Seed data — mirrors mongo-init/init-db.js exactly (ids, balances, branches).
# --------------------------------------------------------------------------
def _seed_documents() -> dict:
    return {
        "users": [
            {"id": 1, "username": "john", "full_name": "John Doe", "role": "CUSTOMER",
             "customer_id": 1, "salt": "85c5d1c480ef3ab5295d33f6f03b1fe1",
             "password_hash": "bbb3cf4f28ef6b73c9cd407e8bf5b61d0e2f35ce5f5171442415cfa78495624a"},
            {"id": 2, "username": "admin", "full_name": "Bank Admin", "role": "ADMIN",
             "customer_id": None, "salt": "5e44222c345264b12914bf0c0c156b33",
             "password_hash": "4c71f3e855013c727b182f1e92711fbbd035bfc539d2b001c641778b96cc5b5d"},
        ],
        "branches": [
            {"id": 1, "name": "Downtown Branch", "city": "New York", "is_active": True},
            {"id": 2, "name": "Uptown Branch", "city": "Boston", "is_active": True},
            {"id": 3, "name": "Westside Branch", "city": "Chicago", "is_active": True},
        ],
        "customers": [
            {"id": 1, "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "phone": "555-0100", "is_active": True},
            {"id": 2, "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@example.com", "phone": "555-0101", "is_active": True},
            {"id": 3, "first_name": "Bob", "last_name": "Johnson", "email": "bob.johnson@example.com", "phone": "555-0102", "is_active": True},
            {"id": 4, "first_name": "Alice", "last_name": "Brown", "email": "alice.brown@example.com", "phone": "555-0103", "is_active": True},
            {"id": 5, "first_name": "Charlie", "last_name": "Wilson", "email": "charlie.wilson@example.com", "phone": "555-0104", "is_active": True},
        ],
        "accounts": [
            {"id": 1, "account_number": "ACC001", "customer_id": 1, "first_name": "John", "last_name": "Doe", "balance": 5000.0, "branch_id": 1, "is_active": True},
            {"id": 2, "account_number": "ACC002", "customer_id": 2, "first_name": "Jane", "last_name": "Smith", "balance": 15000.0, "branch_id": 1, "is_active": True},
            {"id": 3, "account_number": "ACC003", "customer_id": 3, "first_name": "Bob", "last_name": "Johnson", "balance": 7500.0, "branch_id": 2, "is_active": True},
            {"id": 4, "account_number": "ACC004", "customer_id": 4, "first_name": "Alice", "last_name": "Brown", "balance": 20000.0, "branch_id": 2, "is_active": True},
            {"id": 5, "account_number": "ACC005", "customer_id": 5, "first_name": "Charlie", "last_name": "Wilson", "balance": 3200.0, "branch_id": 3, "is_active": True},
        ],
        "transactions": [
            {"id": 1, "from_account_id": 1, "to_account_id": 2, "amount": 100.0, "type": "TRANSFER", "timestamp": datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc)},
            {"id": 2, "from_account_id": 3, "to_account_id": 4, "amount": 500.0, "type": "TRANSFER", "timestamp": datetime(2026, 2, 1, 14, 0, tzinfo=timezone.utc)},
        ],
        "counters": [
            {"_id": "branches", "seq": 3},
            {"_id": "customers", "seq": 5},
            {"_id": "accounts", "seq": 5},
            {"_id": "transactions", "seq": 2},
        ],
    }


def _reseed(database) -> None:
    """Wipe every collection and reinsert the seed. Keeps the same db object so
    that default arguments and app singletons captured at import time stay valid."""
    for name in ("users", "sessions", "branches", "customers",
                 "accounts", "transactions", "counters"):
        database[name].delete_many({})
    for name, docs in _seed_documents().items():
        if docs:
            database[name].insert_many([dict(d) for d in docs])


@pytest.fixture
def fake_db():
    """A freshly seeded in-memory database, shared with the app singletons."""
    _reseed(db_module.db)
    return db_module.db


# --- Repositories wired to the seeded fake database -----------------------

@pytest.fixture
def account_repo(fake_db):
    return AccountRepository(database=fake_db)


@pytest.fixture
def customer_repo(fake_db):
    return CustomerRepository(database=fake_db)


@pytest.fixture
def transaction_repo(fake_db):
    return TransactionRepository(database=fake_db)


@pytest.fixture
def branch_repo(fake_db):
    return BranchRepository(database=fake_db)


# --- Services wired to those repositories ---------------------------------

@pytest.fixture
def account_service(account_repo, customer_repo):
    return AccountService(account_repo, customer_repo)


@pytest.fixture
def customer_service(customer_repo):
    return CustomerService(customer_repo)


@pytest.fixture
def transaction_service(transaction_repo, account_service):
    return TransactionService(transaction_repo, account_service)


# --- FastAPI TestClient, whose singletons share the same fake database -----

@pytest.fixture
def client(fake_db):
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as test_client:
        yield test_client


# --- Login tokens for API tests (Chapter 4 security) -----------------------

@pytest.fixture(autouse=True)
def _reset_login_limiter():
    """Wrong-password counts must not leak from one test into the next."""
    import dependencies
    dependencies.login_limiter.reset()
    yield
    dependencies.login_limiter.reset()


def _auth_header(user) -> dict:
    from security import create_access_token
    return {"Authorization": f"Bearer {create_access_token(user)}"}


@pytest.fixture
def admin_headers():
    from models.user import UserPublic
    return _auth_header(UserPublic(id=2, username="admin", full_name="Bank Admin",
                                   role="ADMIN", customer_id=None))


@pytest.fixture
def john_headers():
    """John is a CUSTOMER who owns customer #1 and account #1 (ACC001)."""
    from models.user import UserPublic
    return _auth_header(UserPublic(id=1, username="john", full_name="John Doe",
                                   role="CUSTOMER", customer_id=1))


# --- Small helper kept from the original scaffold -------------------------

@pytest.fixture
def make_account():
    """Build an Account with sensible defaults; override any field per test."""
    def _make(**overrides) -> Account:
        fields = dict(id=1, account_number="ACC001", customer_id=1, first_name="John",
                      last_name="Doe", balance=1000.0, branch_id=1, is_active=True)
        fields.update(overrides)
        return Account(**fields)
    return _make
