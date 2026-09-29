# services/branch_service.py
# Business/domain logic for branches. Coordinates the repository and raises
# NotFoundError for the controller to translate.
from typing import List

from errors import NotFoundError
from models.branch import Branch, BranchCreate, BranchUpdate
from repository.branch_repository import BranchRepository


class BranchService:
    def __init__(self, repository: BranchRepository = None):
        self._repo = repository or BranchRepository()

    def list_branches(self) -> List[Branch]:
        return self._repo.list_all()

    def get_branch(self, branch_id: int) -> Branch:
        branch = self._repo.get(branch_id)
        if branch is None:
            raise NotFoundError(f"Branch {branch_id} not found")
        return branch

    def create_branch(self, data: BranchCreate) -> Branch:
        branch = Branch(id=0, is_active=True, **data.model_dump())
        return self._repo.add(branch)

    def update_branch(self, branch_id: int, data: BranchUpdate) -> Branch:
        branch = self.get_branch(branch_id)
        changes = data.model_dump(exclude_unset=True)
        updated = branch.model_copy(update=changes)
        return self._repo.update(updated)

    def deactivate_branch(self, branch_id: int) -> Branch:
        """DELETE = deactivate: soft-delete by flipping is_active to False."""
        branch = self.get_branch(branch_id)
        updated = branch.model_copy(update={"is_active": False})
        return self._repo.update(updated)
