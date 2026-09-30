# repository/branch_repository.py
# Data-access layer for branches, stored in the MongoDB "branches" collection.
# No HTTP, no business rules.
from typing import List, Optional

from db import db
from models.branch import Branch
from repository.counters import next_id


class BranchRepository:
    def __init__(self, database=db):
        self._db = database
        self._branches = database["branches"]

    def list_all(self) -> List[Branch]:
        return [Branch(**doc) for doc in self._branches.find({}, {"_id": 0}).sort("id", 1)]

    def get(self, branch_id: int) -> Optional[Branch]:
        doc = self._branches.find_one({"id": branch_id}, {"_id": 0})
        return Branch(**doc) if doc else None

    def add(self, branch: Branch) -> Branch:
        branch.id = next_id("branches", self._db)
        self._branches.insert_one(branch.model_dump())
        return branch

    def update(self, branch: Branch) -> Branch:
        self._branches.update_one({"id": branch.id}, {"$set": branch.model_dump()})
        return branch
