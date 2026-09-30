# repository/user_repository.py
# Data-access layer for login users, stored in the MongoDB "users" collection.
# The users are created by mongo-init/init-db.js when the database container
# first starts. Passwords are stored as a salt + PBKDF2 hash, never plain text.
#   john  / password123  -> customer #1 (John Doe)
#   admin / admin123     -> admin
from typing import Optional

from db import db
from models.user import User


class UserRepository:
    def __init__(self, database=db):
        self._users = database["users"]

    def get(self, user_id: int) -> Optional[User]:
        doc = self._users.find_one({"id": user_id}, {"_id": 0})
        return User(**doc) if doc else None

    def find_by_username(self, username: str) -> Optional[User]:
        doc = self._users.find_one({"username": username}, {"_id": 0})
        return User(**doc) if doc else None