# tests/api/test_security.py
# Chapter 4: API security, tested through the real API (FastAPI TestClient).
#   401 = not logged in / bad token      403 = logged in, but not allowed
#   429 = too many wrong passwords       422 = bad input
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from config import API_KEY, JWT_ALGORITHM, JWT_SECRET

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
ACCOUNTS = "/api/v1/accounts/"
CUSTOMERS = "/api/v1/customers/"
TRANSFER = "/api/v1/transactions/transfer"
REPORT = "/api/v1/analytics/branches/balances"


# ---------- Login + token ----------

def test_login_returns_a_token_that_works(client):
    r = client.post(LOGIN, json={"username": "john", "password": "password123"})
    assert r.status_code == 200
    token = r.json()["token"]

    me = client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["username"] == "john"


def test_wrong_password_is_401(client):
    r = client.post(LOGIN, json={"username": "john", "password": "nope"})
    assert r.status_code == 401


def test_sixth_wrong_password_is_429(client):
    for _ in range(5):
        assert client.post(LOGIN, json={"username": "john", "password": "nope"}).status_code == 401
    r = client.post(LOGIN, json={"username": "john", "password": "password123"})
    assert r.status_code == 429


@pytest.mark.parametrize("headers", [
    {},                                              # no token
    {"Authorization": "Bearer not-a-real-token"},    # garbage token
    {"Authorization": "Basic am9objpwYXNzd29yZDEyMw=="},  # wrong kind of auth
])
def test_missing_or_bad_token_is_401(client, headers):
    assert client.get(ACCOUNTS, headers=headers).status_code == 401


def test_expired_token_is_401(client):
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    token = jwt.encode({"sub": "admin", "uid": 2, "role": "ADMIN", "name": "Bank Admin",
                        "iat": past, "exp": past + timedelta(minutes=60)},
                       JWT_SECRET, algorithm=JWT_ALGORITHM)
    r = client.get(ACCOUNTS, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "expired" in r.json()["detail"]


def test_forged_admin_token_is_401(client):
    fake = jwt.encode({"sub": "hacker", "uid": 99, "role": "ADMIN", "name": "Hacker",
                       "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                      "guessed-secret", algorithm=JWT_ALGORITHM)
    r = client.get(CUSTOMERS, headers={"Authorization": f"Bearer {fake}"})
    assert r.status_code == 401


# ---------- Role-based access: customers vs admins ----------

def test_customer_cannot_create_accounts_403(client, john_headers):
    body = {"customer_id": 1, "first_name": "J", "last_name": "D", "balance": 1000000, "branch_id": 1}
    assert client.post(ACCOUNTS, json=body, headers=john_headers).status_code == 403


def test_customer_cannot_list_all_customers_403(client, john_headers):
    assert client.get(CUSTOMERS, headers=john_headers).status_code == 403


def test_customer_cannot_delete_403(client, john_headers):
    assert client.delete(ACCOUNTS + "2", headers=john_headers).status_code == 403


def test_admin_can_list_all_customers(client, admin_headers):
    r = client.get(CUSTOMERS, headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) == 5


# ---------- Customers only see / change their OWN things ----------

def test_customer_sees_only_own_accounts(client, john_headers):
    r = client.get(ACCOUNTS, headers=john_headers)
    assert [a["account_number"] for a in r.json()] == ["ACC001"]


def test_customer_cannot_read_someone_elses_account_403(client, john_headers):
    assert client.get(ACCOUNTS + "2", headers=john_headers).status_code == 403


def test_customer_can_update_own_profile(client, john_headers):
    r = client.put(CUSTOMERS + "1", json={"phone": "555-0199"}, headers=john_headers)
    assert r.status_code == 200


def test_customer_cannot_update_someone_elses_profile_403(client, john_headers):
    r = client.put(CUSTOMERS + "2", json={"phone": "555-0199"}, headers=john_headers)
    assert r.status_code == 403


def test_directory_shows_names_but_not_balances(client, john_headers):
    r = client.get(ACCOUNTS + "directory", headers=john_headers)
    assert r.status_code == 200
    assert len(r.json()) == 5
    assert "balance" not in r.json()[0]


def test_customer_can_send_from_own_account(client, john_headers, account_repo):
    body = {"from_account_id": 1, "to_account_id": 2, "amount": 100.0}
    assert client.post(TRANSFER, json=body, headers=john_headers).status_code == 201
    assert account_repo.get(1).balance == 4900.0


def test_customer_cannot_send_from_someone_elses_account_403(client, john_headers, account_repo):
    body = {"from_account_id": 2, "to_account_id": 1, "amount": 100.0}   # Jane's money!
    assert client.post(TRANSFER, json=body, headers=john_headers).status_code == 403
    assert account_repo.get(2).balance == 15000.0                        # nothing moved


def test_customer_sees_only_own_transactions(client, john_headers):
    r = client.get("/api/v1/transactions/", headers=john_headers)
    for t in r.json():
        assert 1 in (t["from_account_id"], t["to_account_id"])


# ---------- API key (reports) ----------

def test_report_needs_login_or_api_key_401(client):
    assert client.get(REPORT).status_code == 401


def test_report_with_api_key(client):
    assert client.get(REPORT, headers={"X-API-Key": API_KEY}).status_code == 200


def test_report_with_wrong_api_key_401(client):
    assert client.get(REPORT, headers={"X-API-Key": "guess"}).status_code == 401


def test_report_customer_token_is_403(client, john_headers):
    assert client.get(REPORT, headers=john_headers).status_code == 403


# ---------- Public routes stay public ----------

def test_health_needs_no_login(client):
    assert client.get("/health").status_code == 200
