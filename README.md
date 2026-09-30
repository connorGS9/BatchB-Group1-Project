# BatchB-Group1-Project

**Team:** Antonio · Dmitry · Alexander · Connor · Assim

A full-stack banking system built with **Python (FastAPI)**, **React** and **Node**.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Start the Stack](#start-the-stack)
  - [Stop the Stack](#stop-the-stack)
  - [Reset Everything (Including Data)](#reset-everything-including-data)
- [Testing](#testing)
  - [Project Layout](#project-layout)
  - [Unit Tests](#unit-tests)
  - [Postman API Tests](#postman-api-tests)

---

## Tech Stack

| Layer    | Technology        |
|----------|-------------------|
| Backend  | Python, FastAPI   |
| Frontend | React, Node       |
| Database | MongoDB           |
| Runtime  | Docker Compose    |

---

## Architecture

The backend follows a layered **Controller → Service → Repository (Model)** architecture:

```
Controller  ──>  Service  ──>  Repository (Model)
 (endpoints)    (business logic)   (data access)
```

### Controllers

| Controller           | Responsibility                               |
|----------------------|----------------------------------------------|
| `CustomerController` | Endpoints for the **Customer** model         |
| `AccountController`  | Endpoints for the **Account** model          |
| `AuthController`     | Authentication endpoints (login, tokens)     |

> Each controller handles only the endpoints for its own model, and `AuthController` handles everything related to authentication.

---

## Getting Started

> **Prerequisite:** [Docker](https://docs.docker.com/get-docker/) with Docker Compose installed.

All commands below are run from the **project root directory**.

### Start the Stack

```bash
docker compose up
```

Add `-d` to run it in the background:

```bash
docker compose up -d
```

### Stop the Stack

```bash
docker compose down
```

This stops and removes the containers, but **keeps your database data**.

### Reset Everything (Including Data)

```bash
docker compose down -v
```

> ⚠️ **Warning:** the `-v` flag also deletes the Docker **volumes**, which permanently wipes all database data (customers, accounts, users). Use it when you want a completely fresh start.

To reset and start clean in one go:

```bash
docker compose down -v && docker compose up
```

---

## Testing

### Project Layout

```
banking-api/
├── pytest.ini                  # pytest config (run from banking-api/)
├── requirements-dev.txt        # test-only dependencies
└── tests/
    ├── conftest.py             # shared fixtures: mocked repositories + services wired to them
    └── unit/                   # service-layer unit tests, no MongoDB needed

postman/
├── Bank System API Suite.postman_collection.json
└── Bank System - Local.postman_environment.json   # base_url, customer_id, account_number, account_id, token
```

### Unit Tests

The unit tests cover the **service layer** using mocked repositories, so **no running database is required**.

1. Move into the API folder:
   ```bash
   cd banking-api
   ```
2. Install the app and test dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
3. Run the tests:
   ```bash
   pytest
   ```

### Postman API Tests

The Postman suite runs end-to-end requests against the **live** API.

1. Start the stack from the project root:
   ```bash
   docker compose up
   ```
2. In Postman, **import both files** from the `postman/` folder.
3. Select the **`Bank System - Local`** environment (top-right dropdown).
4. Open **`Bank System API Suite`** and click **Run** to execute the collection.

> 💡 **Tip:** if earlier runs left leftover test data behind, reset with `docker compose down -v` and start the stack again before running the collection.
