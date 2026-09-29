from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

from controllers.account_controller import router as account_router
from controllers.customer_controller import router as customer_router
from controllers.transaction_controller import router as transaction_router
from config import HOST, PORT

app = FastAPI(title="Banking API")

app.include_router(account_router)
app.include_router(customer_router)
app.include_router(transaction_router)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
def dashboard():
    """Serve the live dashboard UI (same origin as the API, so no CORS)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
