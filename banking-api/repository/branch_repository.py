# repository/branch_repository.py
# Data-access layer for branches: in-memory store. No HTTP, no business rules.
from typing import List, Optional

from models.branch import Branch


class BranchRepository:
    def __init__(self):
        # Seeded to match the branch_id values used by the seeded accounts.
        self._branches: List[Branch] = [
            Branch(id=1, name="Downtown Branch", city="New York"),
            Branch(id=2, name="Uptown Branch", city="Boston"),
            Branch(id=3, name="Westside Branch", city="Chicago"),
        ]
        self._next_id = 4

    def list_all(self) -> List[Branch]:
        return self._branches

    def get(self, branch_id: int) -> Optional[Branch]:
        return next((b for b in self._branches if b.id == branch_id), None)

    def add(self, branch: Branch) -> Branch:
        branch.id = self._next_id
        self._next_id += 1
        self._branches.append(branch)
        return branch

    def update(self, branch: Branch) -> Branch:
        for i, existing in enumerate(self._branches):
            if existing.id == branch.id:
                self._branches[i] = branch
                return branch
        return branch
