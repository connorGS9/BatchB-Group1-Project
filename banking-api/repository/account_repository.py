# repository/account_repository.py
# Data-access layer for accounts: owns the in-memory store and the raw
# filtering. Knows nothing about HTTP or business rules.
from typing import List, Optional

from models.account import Account


class AccountRepository:
    def __init__(self):
        self._accounts: List[Account] = [
            Account(id=1, account_number="ACC001", first_name="John", last_name="Doe", balance=5000.00, branch_id=1),
            Account(id=2, account_number="ACC002", first_name="Jane", last_name="Smith", balance=15000.00, branch_id=1),
            Account(id=3, account_number="ACC003", first_name="Bob", last_name="Johnson", balance=7500.00, branch_id=2),
            Account(id=4, account_number="ACC004", first_name="Alice", last_name="Brown", balance=20000.00, branch_id=2),
            Account(id=5, account_number="ACC005", first_name="Charlie", last_name="Wilson", balance=3200.00, branch_id=3),
        ]
        self._next_id = 6

    def list_all(self, branch_id: Optional[int] = None,
                 min_balance: Optional[float] = None) -> List[Account]:
        results = self._accounts
        if branch_id is not None:
            results = [a for a in results if a.branch_id == branch_id]
        if min_balance is not None:
            results = [a for a in results if a.balance >= min_balance]
        return results

    def get(self, account_id: int) -> Optional[Account]:
        return next((a for a in self._accounts if a.id == account_id), None)

    def add(self, account: Account) -> Account:
        account.id = self._next_id
        account.account_number = f"ACC{self._next_id:03d}"
        self._next_id += 1
        self._accounts.append(account)
        return account

    def update(self, account: Account) -> Account:
        for i, existing in enumerate(self._accounts):
            if existing.id == account.id:
                self._accounts[i] = account
                return account
        return account
