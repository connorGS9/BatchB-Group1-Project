# tests/api/test_api.py
# API-layer tests through FastAPI's TestClient. The app's dependencies.py
# singletons share the same mongomock database as the fixtures (see conftest.py),
# so these exercise the real controller -> service -> repository path.

import pytest

ACCOUNTS = "/api/v1/accounts/"
CUSTOMERS = "/api/v1/customers/"
TRANSACTIONS = "/api/v1/transactions/"


# --------------------------------------------------------------------------
# Status codes  (spec behaviour — passes today)
# --------------------------------------------------------------------------
def test_get_existing_account_returns_200(client, admin_headers):
    r = client.get(ACCOUNTS + "1", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["account_number"] == "ACC001"


def test_get_missing_account_returns_404(client, admin_headers):
    assert client.get(ACCOUNTS + "999", headers=admin_headers).status_code == 404


def test_create_account_returns_201(client, admin_headers):
    body = {"customer_id": 1, "first_name": "New", "last_name": "Acct",
            "balance": 250.0, "branch_id": 1}
    r = client.post(ACCOUNTS, json=body, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["id"] == 6
    assert r.json()["account_number"] == "ACC006"


# --------------------------------------------------------------------------
# The two filter endpoints from the spec  (spec behaviour — passes today)
# --------------------------------------------------------------------------
def test_accounts_filter_branch_and_min_balance(client, admin_headers):
    r = client.get(ACCOUNTS, params={"branch_id": 1, "min_balance": 10000}, headers=admin_headers)
    assert r.status_code == 200
    assert [a["id"] for a in r.json()] == [2]


def test_transactions_filter_by_start_date_and_type(client, admin_headers):
    r = client.get(TRANSACTIONS, params={"start_date": "2026-01-20", "type": "TRANSFER"},
                   headers=admin_headers)
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [2]


# --------------------------------------------------------------------------
# BUG #1 — FIXED in Chapter 4 (JWT auth): a write with no Authorization header
# is now rejected with 401.
# --------------------------------------------------------------------------
def test_create_account_without_token_is_rejected(client):
    body = {"customer_id": 1, "first_name": "No", "last_name": "Auth",
            "balance": 0.0, "branch_id": 1}
    r = client.post(ACCOUNTS, json=body)          # no Authorization header
    assert r.status_code == 401


# --------------------------------------------------------------------------
# BUG #1 / #2 — FIXED in Chapter 4: transfers need a login token (401 without),
# and customers can only send from their own account (see the tests below).
# --------------------------------------------------------------------------
def test_transfer_without_token_is_rejected(client):
    body = {"from_account_id": 1, "to_account_id": 2, "amount": 50.0}
    r = client.post(TRANSACTIONS + "transfer", json=body)
    assert r.status_code == 401


# --------------------------------------------------------------------------
# BUG #6 — FIXED in Chapter 4 (input validation): an empty name and the email
# "nope" are now rejected with 422.
# --------------------------------------------------------------------------
def test_create_customer_rejects_blank_name_and_bad_email(client, admin_headers):
    body = {"first_name": "", "last_name": "", "email": "nope", "phone": "x"}
    r = client.post(CUSTOMERS, json=body, headers=admin_headers)
    assert r.status_code in (400, 422)
