from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from controllers.account_controller import router as account_router
from controllers.auth_controller import router as auth_router
from controllers.branch_controller import router as branch_router
from controllers.customer_controller import router as customer_router
from controllers.transaction_controller import router as transaction_router
from config import HOST, PORT
from db import client

app = FastAPI(title="Banking API")

# Let the React frontend (bank-frontend, runs on port 5173) call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account_router)
app.include_router(customer_router)
app.include_router(transaction_router)
app.include_router(branch_router)
app.include_router(auth_router)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
def dashboard():
    """Serve the live dashboard UI (same origin as the API, so no CORS)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    client.admin.command("ping")   # raises if Mongo is unreachable or auth fails
    return {"status": "ok", "mongo": "connected"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)