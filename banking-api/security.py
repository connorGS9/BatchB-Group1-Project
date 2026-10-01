# security.py
# Everything about "who are you?" (authentication) and "what may you do?"
# (authorization) lives here, so the controllers stay short.
#
#   1. create_access_token()  - login hands out a signed JWT
#   2. decode_access_token()  - check the signature and the expiry time
#   3. get_current_user       - FastAPI dependency: no/bad token   -> 401
#   4. require_admin          - FastAPI dependency: not an admin   -> 403
#   5. require_admin_or_api_key - reports: admin token OR the X-API-Key header
#   6. LoginRateLimiter       - too many wrong passwords          -> 429
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from config import (API_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET,
                    LOGIN_BLOCK_SECONDS, LOGIN_MAX_FAILURES)
from errors import AuthError, ForbiddenError, RateLimitError
from models.user import UserPublic

ADMIN = "ADMIN"
CUSTOMER = "CUSTOMER"


# ---------- 1 + 2. JWT: create and check ----------

def create_access_token(user: UserPublic) -> str:
    """Build a JWT that says who the user is and when it stops working.
    The token is SIGNED with JWT_SECRET, so nobody can change the role inside it."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.username,              # "subject" = who this token is for
        "uid": user.id,
        "role": user.role,                 # used for role-based access control
        "customer_id": user.customer_id,
        "name": user.full_name,
        "iat": now,                        # issued at
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),  # expires at
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> UserPublic:
    """Check the signature and expiry, then return the user stored in the token."""
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM],
                            options={"require": ["exp", "sub", "role"]})
    except jwt.ExpiredSignatureError:
        raise AuthError("Your login expired. Please log in again.")
    except jwt.InvalidTokenError:          # bad signature, garbage, missing fields...
        raise AuthError("Invalid login token")
    return UserPublic(id=claims["uid"], username=claims["sub"], full_name=claims["name"],
                      role=claims["role"], customer_id=claims.get("customer_id"))


# ---------- 3 + 4. FastAPI dependencies that protect routes ----------

# HTTPBearer reads the "Authorization: Bearer <token>" header and adds the
# "Authorize" button to Swagger (/docs).
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message,
                         headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> UserPublic:
    """Any logged-in user. No token or a bad token -> 401 Unauthorized."""
    if credentials is None:
        raise _unauthorized("Not logged in")
    try:
        return decode_access_token(credentials.credentials)
    except AuthError as e:
        raise _unauthorized(str(e))


def require_admin(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Logged in AND an admin. A customer gets 403 Forbidden."""
    if user.role != ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user


def is_admin(user: UserPublic) -> bool:
    return user.role == ADMIN


def ensure_own_customer(user: UserPublic, customer_id: int) -> None:
    """Customers may only touch their own customer record. Admins may touch any."""
    if not is_admin(user) and user.customer_id != customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can only access your own details")


# ---------- 5. API key (for programs, not people) ----------

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_admin_or_api_key(
    api_key: Optional[str] = Security(api_key_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> str:
    """Reports can be read by an admin, or by a program sending the X-API-Key header."""
    # compare_digest takes the same time for right and wrong keys (no timing hints)
    if api_key is not None and hmac.compare_digest(api_key, API_KEY):
        return "api-key"
    if api_key is not None:
        raise _unauthorized("Invalid API key")
    return require_admin(get_current_user(credentials)).username


# ---------- 6. Rate limiting ----------

class RateLimiter:
    """General in-memory sliding-window limiter. Remembers the timestamps of
    recent hits per key (e.g. a client IP) and raises RateLimitError once a key
    goes over `max_hits` within `window_seconds`. In-memory on purpose: simple,
    and it resets when the server restarts."""

    def __init__(self, max_hits: int, window_seconds: int, clock=time.monotonic):
        self.max_hits = max_hits
        self.window_seconds = window_seconds
        self._clock = clock
        self._hits: Dict[str, List[float]] = {}

    def _recent(self, key: str) -> List[float]:
        cutoff = self._clock() - self.window_seconds
        recent = [t for t in self._hits.get(key, []) if t > cutoff]
        self._hits[key] = recent
        return recent

    def hit(self, key: str, message: str = "Too many requests. Please try again later.") -> None:
        """Record one request for `key`. If it's already at the cap, record nothing
        and raise RateLimitError so the caller can return 429."""
        recent = self._recent(key)
        if len(recent) >= self.max_hits:
            raise RateLimitError(message)
        recent.append(self._clock())

    def reset(self, key: Optional[str] = None) -> None:
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)


# ---------- 7. Login rate limit ----------

class LoginRateLimiter:
    """Remember wrong passwords per username. After LOGIN_MAX_FAILURES within
    LOGIN_BLOCK_SECONDS, block that username until the oldest failure is old enough.
    Kept in memory: simple, and resets when the server restarts."""

    def __init__(self, max_failures: int = LOGIN_MAX_FAILURES,
                 window_seconds: int = LOGIN_BLOCK_SECONDS, clock=time.monotonic):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures: Dict[str, List[float]] = {}

    def _recent(self, username: str) -> List[float]:
        cutoff = self._clock() - self.window_seconds
        recent = [t for t in self._failures.get(username, []) if t > cutoff]
        self._failures[username] = recent
        return recent

    def check(self, username: str) -> None:
        if len(self._recent(username)) >= self.max_failures:
            raise RateLimitError("Too many failed logins. Try again in a few minutes.")

    def record_failure(self, username: str) -> None:
        self._recent(username).append(self._clock())

    def reset(self, username: Optional[str] = None) -> None:
        if username is None:
            self._failures.clear()
        else:
            self._failures.pop(username, None)
