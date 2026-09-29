# BatchB-Group1-Project
Fullstack system in python, fastapi

## Banking CRUD contribution (Aasim)

The tested account CRUD backend is integrated into the existing `banking-api`
directory. The existing configuration, data file, and layer scaffolding remain
available for group development.

From this repository root in PowerShell:

```powershell
cd banking-api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Swagger: http://127.0.0.1:8000/docs

Run tests from `banking-api`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/verify_live.py
```

The live verifier requires port 8000 to be free and stops its own server afterward.

- [API reference and setup](banking-api/README.md)
- [Word-for-word demonstration guide](banking-api/DEMO_GUIDE.md)
- [Code explanation](banking-api/PROJECT_EXPLANATION.md)

Accounts use hard-coded in-memory data and reset on restart. The existing Flask
and supporting dependencies are retained for compatibility with group work.
