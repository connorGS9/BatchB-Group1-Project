# services/auth_service.py
# Login logic: check the password, hand out a session token, and look up who a
# token belongs to. Users and sessions are stored in MongoDB, so logins survive
# a server restart. (Chapter 5 replaces these tokens with JWTs.)
import hashlib
import hmac
import secrets
from typing import Optional

from errors import AuthError
from models.user import User, UserPublic
from repository.session_repository import SessionRepository
from repository.user_repository import UserRepository


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000).hex()


def to_public(user: User) -> UserPublic:
    return UserPublic(**user.model_dump(exclude={"salt", "password_hash"}))


class AuthService:
    def __init__(self, repository: UserRepository = None, sessions: SessionRepository = None):
        self._repo = repository or UserRepository()
        self._sessions = sessions or SessionRepository()

    def login(self, username: str, password: str) -> dict:
        user = self._repo.find_by_username(username.strip().lower())
        # Same message for "no such user" and "wrong password" so nobody can
        # use the login form to find out which usernames exist.
        if user is None or not hmac.compare_digest(
            hash_password(password, user.salt), user.password_hash
        ):
            raise AuthError("Incorrect username or password")
        token = secrets.token_urlsafe(32)
        self._sessions.create(token, user.id)
        return {"token": token, "user": to_public(user)}

    def current_user(self, token: Optional[str]) -> UserPublic:
        user_id = self._sessions.get_user_id(token) if token else None
        user = self._repo.get(user_id) if user_id else None
        if user is None:
            raise AuthError("You're not logged in, or your session expired")
        return to_public(user)

    def logout(self, token: Optional[str]) -> None:
        if token:
            self._sessions.delete(token)