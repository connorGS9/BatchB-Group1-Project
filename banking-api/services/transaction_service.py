# services/transaction_service.py
# Business logic for transactions. A transfer coordinates two account balance
# changes and records a ledger entry. Depends on AccountService so balances and
# the accounts endpoints stay consistent.
from datetime import datetime
from typing import List, Optional
from datetime import date

from errors import ValidationError
from models.transaction import Transaction, TransactionType, TransferRequest
from repository.transaction_repository import TransactionRepository
from services.account_service import AccountService


class TransactionService:
    def __init__(self, repository: TransactionRepository, account_service: AccountService):
        self._repo = repository
        self._accounts = account_service

    def list_transactions(self, start_date: Optional[date] = None,
                          type: Optional[TransactionType] = None) -> List[Transaction]:
        return self._repo.list_all(start_date=start_date, type=type)

    def transfer(self, data: TransferRequest) -> Transaction:
        if data.amount <= 0:
            raise ValidationError("Transfer amount must be positive")
        if data.from_account_id == data.to_account_id:
            raise ValidationError("Cannot transfer to the same account")

        # Both must exist (raises NotFoundError) and be active with funds.
        source = self._accounts.get_account(data.from_account_id)
        target = self._accounts.get_account(data.to_account_id)
        # Check BOTH accounts before any money moves, so a failed transfer
        # can never take money out of the sender without paying the receiver.
        if not source.is_active:
            raise ValidationError(f"Account {data.from_account_id} is inactive")
        if not target.is_active:
            raise ValidationError(f"Account {data.to_account_id} is inactive")
        if source.balance < data.amount:
            raise ValidationError(
                f"Insufficient funds in account {data.from_account_id}")

        # Move the money, then record the entry.
        self._accounts.adjust_balance(data.from_account_id, -data.amount)
        self._accounts.adjust_balance(data.to_account_id, data.amount)

        transaction = Transaction(
            id=0,
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            amount=data.amount,
            type=TransactionType.TRANSFER,
            timestamp=datetime.now(),
        )
        return self._repo.add(transaction)
