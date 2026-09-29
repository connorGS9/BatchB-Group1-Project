# Banking REST API

A small Python/FastAPI backend for the assignment: **“Use REST API to create a backend of Banking Application with Hard-coded data. Language: Python or Java. Use or Demo CRUD Operation.”**

The API manages accounts using JSON and demonstrates create, read, update, and delete operations. Three fictional accounts are initialized in memory. There is no database, authentication, or frontend.

## Quick start (Windows PowerShell)

Use Python 3.14 (the tested version). From the group repository, first run `cd banking-api`, then:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

No virtual-environment activation is required. Stop with **Ctrl+C**. On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows executable.

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json
- Status: http://127.0.0.1:8000/

Swagger's JavaScript/CSS assets require internet access. Use one server process: memory is private to each process. Restarting (including development reloads) restores the three samples and removes all changes.

## Architecture and technologies

```text
Swagger / HTTP client -> Uvicorn -> FastAPI routing
                                  -> Pydantic validation
                                  -> in-memory account dictionary
                                  -> JSON response + HTTP status
```

Python provides the application logic and exact `Decimal` amounts. FastAPI handles HTTP routing and OpenAPI documentation. Pydantic defines and validates schemas. Uvicorn serves the app. pytest and FastAPI TestClient run automated tests; HTTPX supports live HTTP verification. The group's existing Flask dependencies are also preserved. Exact dependency versions are pinned in `requirements.txt`.

`app/models.py` contains the schemas, and `app/main.py` contains all six routes and the app factory. `tests/test_api.py` tests fresh app instances. `scripts/verify_live.py` starts a real server and checks HTTP behavior. See [the code walkthrough](PROJECT_EXPLANATION.md) and [the presentation script](DEMO_GUIDE.md).

## Account model

| Field | Rules |
| --- | --- |
| `id` | Server-assigned positive integer; cannot be supplied in POST/PUT bodies |
| `account_holder` | String, trimmed, 1–100 characters after trimming |
| `account_type` | Exactly `checking` or `savings` |
| `balance` | Nonnegative finite decimal, at most 10 integer digits and 2 decimal places |

All three editable fields are required. Unknown fields are rejected. Balance input accepts JSON numbers or decimal strings; examples use strings to preserve decimal precision. Responses always use strings with two decimal places. Invalid precision is rejected rather than rounded. This is an educational account-record API; changing the balance is a record update, not a transfer or ledger transaction.

Samples: Avery Johnson (checking, 1250.50), Jordan Patel (savings, 8400.00), Morgan Lee (checking, 675.25), with IDs 1–3. New IDs start at 4 and are not reused during the process lifetime.

## Endpoints

| Method | Endpoint | Meaning | Success | Errors |
| --- | --- | --- | --- | --- |
| GET | `/` | Welcome/status | 200 | — |
| GET | `/accounts` | Read all accounts | 200, JSON array | — |
| GET | `/accounts/{id}` | Read one account | 200, account | 404, 422 |
| POST | `/accounts` | Create an account | 201, account and Location header | 422 |
| PUT | `/accounts/{id}` | Replace all editable fields | 200, account | 404, 422 |
| DELETE | `/accounts/{id}` | Remove an account | 204, empty body | 404, 422 |

`200` means success, `201` means created, `204` means success without a response body, `404` means no account has that ID, and `422` means invalid request data. IDs must be positive integers. PUT preserves the ID and requires a complete body; it does not create missing accounts. GET/DELETE send no request body. An empty collection returns `[]`.

## Example requests and responses

In PowerShell:

```powershell
$base = 'http://127.0.0.1:8000'
Invoke-RestMethod "$base/"
Invoke-RestMethod "$base/accounts"
Invoke-RestMethod "$base/accounts/1"
$body = '{"account_holder":"Taylor Brown","account_type":"savings","balance":"500.00"}'
$created = Invoke-RestMethod "$base/accounts" -Method Post -ContentType 'application/json' -Body $body
$id = $created.id
Invoke-RestMethod "$base/accounts/$id"
$update = '{"account_holder":"Taylor Brown","account_type":"savings","balance":"750.25"}'
Invoke-RestMethod "$base/accounts/$id" -Method Put -ContentType 'application/json' -Body $update
Invoke-RestMethod "$base/accounts/$id" -Method Delete
```

GET `/` returns `200`:

```json
{"message":"Welcome to the Banking REST API","status":"ok","docs":"/docs"}
```

POST returns `201` and `Location: /accounts/4` on a fresh server:

```json
{"account_holder":"Taylor Brown","account_type":"savings","balance":"500.00","id":4}
```

GET the new account returns that same object with `200`. PUT returns the same fields with `"balance":"750.25"` and `200`. DELETE returns `204` with **no JSON body**. GET the deleted account returns `404`:

```json
{"detail":"Account 4 not found"}
```

Submitting a negative balance produces `422` with a `detail` array identifying `body.balance` and explaining that it must be greater than or equal to zero. Missing fields, blank names, unknown account types, extra fields, malformed JSON, and invalid IDs also produce validation errors.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/verify_live.py
.\.venv\Scripts\python.exe -m pip check
```

The live verifier needs port 8000 free. It launches and stops only its own server. Automated tests cover all endpoints, missing records, validation with unchanged storage, exact money formatting, repeated PUT, deletion, ID allocation, full CRUD, documentation, and fresh-app resets. No database or HTTP mocks are used. Live checks additionally send requests over an actual TCP connection and verify Swagger HTML, its assets, and OpenAPI.

## Scope

This intentionally satisfies a hard-coded-data training assignment. It is not a production banking system. A future persistent version could replace dictionary operations with database transactions while retaining the request/response schemas. Authentication, authorization, audit trails, and a transaction ledger would belong to that separate production design.

## References

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI response status codes](https://fastapi.tiangolo.com/tutorial/response-status-code/)
- [Pydantic field constraints](https://docs.pydantic.dev/latest/concepts/fields/)
