# BatchB-Group1-Project
***Antonio, Dmitry, Alexander, Connor, Assim***

Fullstack system in python, using fastapi, react, node.

# Controller --> Service --> Repository (Model) architecture
Controller package: CustomerController, AccountController, AuthController 
***Each handles the endpoints relating to the specific model and auth handles auth endpoints***

# Run by using the command: 'docker compose up' from the root directory

# Testing
```
banking-api/
  pytest.ini                  # pytest config (run from banking-api/)
  requirements-dev.txt        # test-only dependencies
  tests/
    conftest.py               # shared fixtures: mocked repositories + services wired to them
    unit/                     # service-layer unit tests, no MongoDB needed
postman/
  Bank System API Suite.postman_collection.json
  Bank System - Local.postman_environment.json   # base_url, customer_id, account_number, account_id, token
```
**Unit tests:** `cd banking-api`, `pip install -r requirements.txt -r requirements-dev.txt`, then `pytest`.

**Postman:** import both files from `postman/`, select the *Bank System - Local* environment, and run the collection with the stack up (`docker compose up`).
