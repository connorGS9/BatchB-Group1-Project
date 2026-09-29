"""Exercise real routing, validation, serialization, and storage without mocks."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def payload():
    return {"account_holder": "Taylor Brown", "account_type": "savings", "balance": "500.00"}


def test_welcome(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Banking REST API", "status": "ok", "docs": "/docs"}


def test_list_accounts(client):
    response = client.get("/accounts")
    assert response.status_code == 200
    assert [a["id"] for a in response.json()] == [1, 2, 3]


def test_get_account(client):
    response = client.get("/accounts/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "account_holder": "Avery Johnson", "account_type": "checking", "balance": "1250.50"}


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_account(client, payload, method):
    kwargs = {"json": payload} if method == "put" else {}
    response = getattr(client, method)("/accounts/999", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "Account 999 not found"}


def test_create_account(client, payload):
    response = client.post("/accounts", json=payload)
    assert response.status_code == 201
    assert response.json() == {"id": 4, **payload}
    assert response.headers["location"] == "/accounts/4"
    assert len(client.get("/accounts").json()) == 4


def test_update_account(client, payload):
    response = client.put("/accounts/1", json=payload)
    assert response.status_code == 200
    assert response.json() == {"id": 1, **payload}
    assert client.get("/accounts/1").json() == response.json()
    assert client.put("/accounts/1", json=payload).json() == response.json()


def test_delete_account(client):
    response = client.delete("/accounts/1")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/accounts/1").status_code == 404
    assert client.delete("/accounts/1").status_code == 404


@pytest.mark.parametrize("change", [
    {"account_holder": "   "}, {"account_holder": "x" * 101},
    {"account_holder": 123}, {"account_type": "credit"},
    {"balance": "-1"}, {"balance": "1.001"}, {"balance": "NaN"},
    {"balance": "Infinity"}, {"balance": "10000000000.00"},
    {"balance": "money"}, {"balance": None}, {"id": 9},
])
@pytest.mark.parametrize("method,path", [("post", "/accounts"), ("put", "/accounts/1")])
def test_invalid_input_does_not_mutate(client, payload, change, method, path):
    before = client.get("/accounts").json()
    response = getattr(client, method)(path, json={**payload, **change})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert client.get("/accounts").json() == before


def test_required_fields_and_malformed_json(client):
    assert client.post("/accounts", json={}).status_code == 422
    assert client.put("/accounts/1", json={"balance": "5"}).status_code == 422
    assert client.post("/accounts", content="{", headers={"Content-Type": "application/json"}).status_code == 422


@pytest.mark.parametrize("account_id", ["0", "-1", "abc"])
def test_invalid_path(client, account_id):
    assert client.get(f"/accounts/{account_id}").status_code == 422


def test_zero_balance_and_trimmed_name(client, payload):
    response = client.post("/accounts", json={**payload, "account_holder": " Taylor Brown ", "balance": 0})
    assert response.status_code == 201
    assert response.json()["balance"] == "0.00"
    assert response.json()["account_holder"] == "Taylor Brown"


def test_full_crud_lifecycle(client, payload):
    created = client.post("/accounts", json=payload)
    assert created.status_code == 201
    path = created.headers["location"]
    assert client.get(path).json() == created.json()
    updated = client.put(path, json={**payload, "balance": "750.25"})
    assert updated.status_code == 200
    assert client.get(path).json()["balance"] == "750.25"
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.post("/accounts", json=payload).json()["id"] == 5


def test_docs_and_openapi(client):
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "swagger-ui" in docs.text
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {"/", "/accounts", "/accounts/{id}"}
    assert "201" in schema["paths"]["/accounts"]["post"]["responses"]
    assert "content" not in schema["paths"]["/accounts/{id}"]["delete"]["responses"]["204"]


def test_new_app_resets_data(client):
    client.delete("/accounts/1")
    with TestClient(create_app()) as fresh:
        assert fresh.get("/accounts/1").status_code == 200
        assert len(fresh.get("/accounts").json()) == 3


def test_group_entry_point():
    from main import app

    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert len(client.get("/accounts").json()) == 3
        assert client.get("/docs").status_code == 200
