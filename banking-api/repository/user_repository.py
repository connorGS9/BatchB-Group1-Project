# repository/user_repository.py
# Data-access layer for login users. Passwords are never stored in plain text:
# each user has a random salt and a PBKDF2 hash of (password + salt).
#   john  / password123  -> customer #1 (John Doe)
#   admin / admin123     -> admin
from typing import List, Optional

from models.user import User


class UserRepository:
    def __init__(self):
        self._users: List[User] = [
            User(id=1, username="john", full_name="John Doe", role="CUSTOMER", customer_id=1,
                 salt="85c5d1c480ef3ab5295d33f6f03b1fe1",
                 password_hash="bbb3cf4f28ef6b73c9cd407e8bf5b61d0e2f35ce5f5171442415cfa78495624a"),
            User(id=2, username="admin", full_name="Bank Admin", role="ADMIN",
                 salt="5e44222c345264b12914bf0c0c156b33",
                 password_hash="4c71f3e855013c727b182f1e92711fbbd035bfc539d2b001c641778b96cc5b5d"),
        ]

    def get(self, user_id: int) -> Optional[User]:
        return next((u for u in self._users if u.id == user_id), None)

    def find_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self._users if u.username == username), None)