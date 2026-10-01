# services/account_service.py
# Business/domain logic for accounts. Coordinates the repository and enforces
# rules, raising NotFoundError / ValidationError for the controller to translate.
from typing import List, Optional

from errors import NotFoundError, ValidationError
from models.account import Account, AccountCreate, AccountUpdate
from repository.account_repository import AccountRepository
from repository.branch_repository import BranchRepository
from repository.customer_repository import CustomerRepository


class AccountService:
    def __init__(self, repository: AccountRepository = None,
                 customer_repository: CustomerRepository = None,
                 branch_repository: BranchRepository = None):
        self._repo = repository or AccountRepository()
        # Used to verify an account's customer_id points at a real, active customer.
        self._customers = customer_repository
        # Used to verify an account's branch_id points at a real, active branch.
        self._branches = branch_repository or BranchRepository()

    def list_accounts(self, branch_id: Optional[int] = None,
                      min_balance: Optional[float] = None,
                      customer_id: Optional[int] = None) -> List[Account]:
        return self._repo.list_all(branch_id=branch_id, min_balance=min_balance,
                                   customer_id=customer_id)

    def get_account(self, account_id: int) -> Account:
        account = self._repo.get(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")
        return account

    def create_account(self, data: AccountCreate) -> Account:
        if data.balance < 0:
            raise ValidationError("Opening balance cannot be negative")
        if self._customers is not None:
            customer = self._customers.get(data.customer_id)
            if customer is None:
                raise ValidationError(f"Customer {data.customer_id} does not exist")
            if not customer.is_active:
                raise ValidationError(f"Customer {data.customer_id} is inactive")
        # The branch must exist and be open to accept new accounts.
        branch = self._branches.get(data.branch_id)
        if branch is None or not branch.is_active:
            raise ValidationError(f"Branch {data.branch_id} does not exist or is inactive")
        account = Account(id=0, account_number="", is_active=True, **data.model_dump())
        return self._repo.add(account)

    def update_account(self, account_id: int, data: AccountUpdate) -> Account:
        account = self.get_account(account_id)
        changes = data.model_dump(exclude_unset=True)
        updated = account.model_copy(update=changes)
        return self._repo.update(updated)

    def deactivate_account(self, account_id: int) -> Account:
        """DELETE = deactivate: soft-delete by flipping is_active to False."""
        account = self.get_account(account_id)
        updated = account.model_copy(update={"is_active": False})
        return self._repo.update(updated)

    def adjust_balance(self, account_id: int, delta: float) -> Account:
        """Apply a signed change to an account's balance. Used by transfers.
        Rejects inactive accounts and overdrafts."""
        account = self.get_account(account_id)
        if not account.is_active:
            raise ValidationError(f"Account {account_id} is inactive")
        # Move the money through the repository's single atomic operation rather than
        # a read-modify-write, so overlapping changes can't clobber each other.
        updated = self._repo.adjust_balance(account_id, delta)
        if updated is None:
            raise ValidationError(f"Insufficient funds in account {account_id}")
        return updated
