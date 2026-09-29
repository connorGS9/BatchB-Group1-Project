# Understanding the finished project

## Start with the big picture

The server holds a dictionary of account objects. A client asks to read or change those objects using HTTP. FastAPI chooses a Python function based on the HTTP method and URL. Pydantic checks the data. The function operates on the dictionary, and FastAPI sends the result as JSON.

An account looks like this in a response:

```json
{"id":1,"account_holder":"Avery Johnson","account_type":"checking","balance":"1250.50"}
```

These names and amounts are fictional training data.

## Every project file

| File | Purpose |
| --- | --- |
| `main.py` | Preserves the group startup entry point and exposes the completed FastAPI app. |
| `app/__init__.py` | Marks `app` as a Python package. |
| `app/models.py` | Defines the account input and output schemas and exact balance formatting. |
| `app/main.py` | Creates the app, sample dictionary, ID counter, helper, and six endpoint handlers. |
| `tests/test_api.py` | Automated tests for route behavior, validation, persistence within an instance, and reset between instances. |
| `scripts/verify_live.py` | Starts a real server, verifies HTTP responses and documentation assets, and stops that process. |
| `requirements.txt` | Pins the installed application and test dependencies, including their supporting packages. |
| `.gitignore` | Keeps virtual environments, caches, IDE files, logs, build outputs, and common secret files out of Git. |
| `README.md` | Setup, architecture, model, endpoints, examples, and test commands. |
| `DEMO_GUIDE.md` | Timed demonstration, exact clicks and bodies, spoken script, and instructor questions. |
| `PROJECT_EXPLANATION.md` | This beginner-friendly code walkthrough. |

Generated `.venv`, `__pycache__`, and `.pytest_cache` directories are local development artifacts and ignored by Git. `.git` contains version history and remote configuration rather than application code.

## The schemas in models.py

`AccountInput` extends Pydantic’s `BaseModel`. It describes the three fields a client can submit. A type hint such as `account_holder: str` states the expected data type. `Annotated` attaches extra validation metadata to that type.

- `StringConstraints` trims the name and checks its length is 1–100, rejecting whitespace-only names.
- `Literal["checking", "savings"]` allows only those two exact values.
- `Decimal` stores balance using decimal arithmetic. `Field` requires a finite value greater than or equal to zero, with at most 12 total digits, at most 2 decimal places, and at most 10 integer digits. Invalid precision is rejected, not silently rounded.
- `ConfigDict(extra="forbid")` rejects unexpected fields, including a client-supplied ID.
- `serialize_balance()` is a field serializer: it emits the decimal as a JSON string with exactly two decimal places. It does not change the stored amount.

`Account` inherits those fields and adds a positive integer `id`. Inheritance avoids repeating the same validation rules. The server constructs this response model after assigning an ID. `payload.model_dump()` produces Python field values (including Decimal); `**` expands that dictionary into keyword arguments for `Account(...)`.

## App creation and storage

`create_app()` returns a new FastAPI application. It creates a dictionary where IDs 1, 2, and 3 map to sample `Account` objects and sets `next_id = 4`. The nested route functions can access this dictionary: their enclosing function’s variables stay available through a Python closure.

Each test calls the factory to get isolated data. The module-level `app = create_app()` constructs the application. In the startup command, `main:app` tells Uvicorn to import `banking-api/main.py` and serve its `app` variable. That group entry point imports the completed application from `app/main.py`.

`next_id` increases after every successful creation. Deleting a record does not decrease it, so deleted IDs are not reused within that application instance. The `nonlocal next_id` statement lets `create_account()` update the counter in its enclosing function.

This storage is temporary. A restart creates a new dictionary. Run one worker; multiple processes would have independent dictionaries. The handlers are `async def` and have no internal `await` points, so these short in-memory operations do not yield midway to another request on the same event loop. That is sufficient for this small single-process example, not a substitute for database transaction guarantees.

## Routing and CRUD

The lines starting with `@api.get`, `@api.post`, `@api.put`, and `@api.delete` are decorators. They register the function below them as the handler for a method and path. The tags group operations in Swagger. `response_model` defines and checks the response schema. `status_code` selects a success status when it differs from the default 200.

`AccountId` is a reusable annotated integer type with a positive-value path constraint. The `{id}` placeholder matches the function argument `id`. Python has a built-in named `id`; here the parameter deliberately matches the assignment’s URL placeholder and is used only inside the handler.

`require_account()` is the shared lookup helper. It returns an account or raises `HTTPException(404, detail=...)`. Raising stops the handler and lets FastAPI generate a useful JSON error. `NOT_FOUND` adds that response description to OpenAPI; the helper implements the actual behavior.

| Function | Behavior |
| --- | --- |
| `welcome()` | Returns the API message, status, and docs path. |
| `list_accounts()` | Returns dictionary values as a list. If all records are deleted, the list is empty. |
| `get_account()` | Uses the helper to fetch one account or report 404. |
| `create_account()` | Builds an Account using the next ID, stores it, increments the counter, sets Location, and returns 201. |
| `update_account()` | Requires an existing ID, replaces every editable field using validated input, and returns 200. |
| `delete_account()` | Requires an existing ID, removes it with `del`, and explicitly returns an empty 204 Response. |

PUT uses the same input schema as POST, so every editable field is mandatory. It preserves the ID and never creates a missing record. Repeating an identical PUT leaves the same state. DELETE is also idempotent in its final effect: a resource stays absent, even though the first request returns 204 and later attempts return 404.

## Follow one request

1. Swagger sends `POST /accounts` with JSON for Taylor Brown’s savings account and `"500.00"` balance.
2. Uvicorn receives the network request and passes it to FastAPI.
3. FastAPI matches the POST route and asks Pydantic to construct `AccountInput`.
4. Pydantic trims/checks the name, checks the account type, parses the decimal, checks constraints, and rejects unknown fields. If this fails, FastAPI returns 422 before calling the handler.
5. `create_account()` builds `Account(id=4, ...)`, stores it, and advances the counter to 5.
6. FastAPI applies the response model and JSON serializer. The client receives 201, `Location: /accounts/4`, and the complete account object.
7. A later GET reads the same dictionary entry. PUT replaces it; DELETE removes it.

Path validation also happens before a handler runs: `/accounts/abc` and `/accounts/0` produce 422. A valid positive ID without a record produces 404. A request containing both a missing ID and an invalid body can produce 422 first, because request validation precedes the existence check.

## HTTP responses

Successful reads and updates return 200. Creation returns 201. Deletion returns 204 with zero body bytes, not `null` or `{}`. Missing records return a JSON `detail` message and 404. Invalid input returns 422 with a `detail` list containing error locations and explanations. Requests use JSON Content-Type for POST and PUT; GET and DELETE have no bodies in this API.

Swagger at `/docs` uses `/openapi.json` to display the routes and schemas. The page fetches its UI assets from a CDN, so its interactive display requires internet access.

## How the tests establish correctness

The `client` pytest fixture creates a fresh app and wraps it in FastAPI’s `TestClient`. Requests pass through the real routing, validation, serialization, and dictionary logic inside the process; they do not use mocked handlers. The context manager closes the client afterward. The `payload` fixture supplies a reusable valid input dictionary.

Tests assert both status codes and meaningful response contents. Parametrization runs the same assertion against multiple invalid values or methods; that is why the number of executed cases exceeds the number of test functions. Validation tests snapshot the collection and confirm failed POST/PUT requests leave it unchanged. Other tests verify the full CRUD lifecycle, repeated PUT, deletion followed by 404, unique IDs after deletion, exact money output, valid zero balances, and fresh sample data in a new app.

`test_docs_and_openapi` checks the documentation HTML and generated schema, including the empty 204 response contract. The separate live verification script binds a probe socket to check port availability, launches Uvicorn using the virtual environment’s interpreter, waits for startup, and sends actual TCP HTTP requests. It verifies Swagger HTML, reachable JavaScript/CSS assets, OpenAPI, sample reads, the whole CRUD lifecycle, validation, and missing-record responses. Its `finally` block stops only the process it launched, even if a check fails. It checks HTTP delivery of Swagger; it does not automate browser rendering.

Run the automated suite with `.\.venv\Scripts\python.exe -m pytest -q`. Run live verification with `.\.venv\Scripts\python.exe scripts/verify_live.py` while port 8000 is free. The tested suite contains 42 cases. The dependency set includes HTTPX for the live script and HTTPX2, used by the installed Starlette TestClient.

## How to study in 15 minutes

Read `models.py` first to learn the data rules. Read `main.py` from the factory to the routes. Follow the POST flow above, then compare PUT and DELETE. Read the full lifecycle test to see the expected behavior in executable form. Finally rehearse the demo guide once with a fresh server.

## Preserved group files

Paths above are relative to `banking-api`. The repository root README links to this contribution; its `.gitignore` is shared. The original `config.py`, `data/fakeData.json`, and `blank.py` files under controllers, models, repository, and services remain unchanged. They are empty scaffolding reserved for group work. Existing requirements, including Flask, are retained. The original welcome-only `main.py` now imports the completed app, extending the welcome response with status/docs fields and exposing all CRUD routes. Teammate branches have not been merged or modified.
