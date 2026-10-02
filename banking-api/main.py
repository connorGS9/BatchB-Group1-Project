from fastapi import FastAPI
from contextlib import asynccontextmanager
from pymongo.errors import PyMongoError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from controllers.account_controller import router as account_router
from controllers.analytics_controller import router as analytics_router
from controllers.application_controller import router as application_router
from controllers.auth_controller import router as auth_router
from controllers.branch_controller import router as branch_router
from controllers.customer_controller import router as customer_router
from controllers.transaction_controller import router as transaction_router
from config import CORS_ORIGINS, HOST, PORT
from db import client, ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_indexes()
    except PyMongoError as e:  # don't block startup; /health will report Mongo problems
        print(f"Warning: could not create indexes: {e}")
    yield


app = FastAPI(title="Banking API", lifespan=lifespan)

# Let the React frontend call this API from the browser. The allowed sites come
# from CORS_ORIGINS (config.py): localhost:5173 on your laptop, the CloudFront URL on AWS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account_router)
app.include_router(customer_router)
app.include_router(transaction_router)
app.include_router(branch_router)
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(application_router)

@app.get("/", include_in_schema=False)
def root():
    """API-only origin. The UI is the React app, served separately (nginx/Vite)."""
    return {"service": "Banking API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    client.admin.command("ping")   # raises if Mongo is unreachable or auth fails
    return {"status": "ok", "mongo": "connected"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)