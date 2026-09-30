# services/auth_service.py
# Login logic: check the password, then hand out a JWT (see security.py).
# A JWT is "stateless": the server doesn't store it. It checks the signature and
# the expiry time on every request instead, so there's no sessions collection.
import hashlib
import hmac
from typing import Optional

from errors import AuthError
from models.user import User, UserPublic
from repository.user_repository import UserRepository
from security import LoginRateLimiter, create_access_token, decode_access_token


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000).hex()


def to_public(user: User) -> UserPublic:
    return UserPublic(**user.model_dump(exclude={"salt", "password_hash"}))


class AuthService:
    def __init__(self, repository: UserRepository = None, limiter: LoginRateLimiter = None):
        self._repo = repository or UserRepository()
        self._limiter = limiter or LoginRateLimiter()

    def login(self, username: str, password: str) -> dict:
        username = username.strip().lower()
        self._limiter.check(username)            # too many wrong passwords -> 429
        user = self._repo.find_by_username(username)
        # Same message for "no such user" and "wrong password" so nobody can
        # use the login form to find out which usernames exist.
        if user is None or not hmac.compare_digest(
            hash_password(password, user.salt), user.password_hash
        ):
            self._limiter.record_failure(username)
            raise AuthError("Incorrect username or password")
        self._limiter.reset(username)
        public = to_public(user)
        return {"token": create_access_token(public), "token_type": "bearer", "user": public}

    def current_user(self, token: Optional[str]) -> UserPublic:
        if not token:
            raise AuthError("You're not logged in")
        return decode_access_token(token)
