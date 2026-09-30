# repository/session_repository.py
# Data-access layer for login sessions, stored in the MongoDB "sessions" collection.
# One document per signed-in browser: { token, user_id, created_at }.
#   login  -> create()       (Create)
#   /me    -> get_user_id()  (Read)
#   logout -> delete()       (Delete)
from datetime import datetime, timezone
from typing import Optional

from db import db


class SessionRepository:
    def __init__(self, database=db):
        self._sessions = database["sessions"]

    def create(self, token: str, user_id: int) -> None:
        self._sessions.insert_one(
            {"token": token, "user_id": user_id, "created_at": datetime.now(timezone.utc)}
        )

    def get_user_id(self, token: str) -> Optional[int]:
        doc = self._sessions.find_one({"token": token})
        return doc["user_id"] if doc else None

    def delete(self, token: str) -> None:
        self._sessions.delete_one({"token": token})