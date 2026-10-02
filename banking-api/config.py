import os
from dotenv import load_dotenv

load_dotenv()
PORT = 8000
HOST = "0.0.0.0"
DEBUG = True

MONGO_URL = os.environ["MONGO_URL"]          # KeyError on startup if not set; better than a silent default
MONGO_DB = os.getenv("MONGO_DB", "banking")  # a db name isn't secret, so a default is fine

# Websites allowed to call this API from a browser (CORS). Comma-separated.
# Locally that's the Vite/Docker site; on AWS it's the CloudFront URL, e.g.
#   CORS_ORIGINS=https://d123abc.cloudfront.net
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

# ---------- Security (Chapter 4) ----------
# Secrets come from environment variables (.env locally, compose.yaml in Docker),
# never from the code, so they are not pushed to GitHub.
JWT_SECRET = os.environ["JWT_SECRET"]        # signs login tokens; anyone who has it can forge a login
JWT_ALGORITHM = "HS256"                      # HMAC + SHA-256 signature
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))  # a token only works for 1 hour
API_KEY = os.environ["API_KEY"]              # lets other programs read the reports without a login

# Login rate limit: after this many wrong passwords, that username is blocked for a while.
LOGIN_MAX_FAILURES = 5
LOGIN_BLOCK_SECONDS = 5 * 60
