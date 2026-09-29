# services/account_service.py
# Business/domain logic for accounts. Coordinates the repository and enforces
# rules, raising NotFoundError / ValidationError for the controller to translate.
from typing import List, Optional

from errors import NotFoundError, ValidationError
from models.account import Account, AccountCreate, AccountUpdate
from repository.account_repository import AccountRepository
from repository.customer_repository import CustomerRepository


class AccountService:
    def __init__(self, repository: AccountRepository = None,
                 customer_repository: CustomerRepository = None):
        self._repo = repository or AccountRepository()
        # Used to verify an account's customer_id points at a real customer.
        self._customers = customer_repository

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
        if self._customers is not None and self._customers.get(data.customer_id) is None:
            raise ValidationError(f"Customer {data.customer_id} does not exist")
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
        new_balance = account.balance + delta
        if new_balance < 0:
            raise ValidationError(f"Insufficient funds in account {account_id}")
        updated = account.model_copy(update={"balance": new_balance})
        return self._repo.update(updated)
