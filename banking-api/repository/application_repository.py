# repository/application_repository.py
# Data-access layer for account-opening applications, stored in the MongoDB
# "applications" collection. No HTTP, no business rules.
from typing import List, Optional

from db import db
from models.application import Application
from repository.counters import next_id


class ApplicationRepository:
    def __init__(self, database=db):
        self._db = database
        self._apps = database["applications"]

    def list_all(self, status: Optional[str] = None) -> List[Application]:
        query = {} if status is None else {"status": status}
        return [Application(**doc) for doc in self._apps.find(query, {"_id": 0}).sort("id", 1)]

    def get(self, app_id: int) -> Optional[Application]:
        doc = self._apps.find_one({"id": app_id}, {"_id": 0})
        return Application(**doc) if doc else None

    def find_pending(self, email: str, username: str) -> Optional[Application]:
        """An existing PENDING application for this email OR username, if any.
        Used to stop one person from stacking up several open applications."""
        doc = self._apps.find_one(
            {"status": "PENDING", "$or": [{"email": email}, {"username": username}]},
            {"_id": 0},
        )
        return Application(**doc) if doc else None

    def add(self, application: Application) -> Application:
        application.id = next_id("applications", self._db)
        self._apps.insert_one(application.model_dump())
        return application

    def update(self, application: Application) -> Application:
        self._apps.update_one({"id": application.id}, {"$set": application.model_dump()})
        return application
