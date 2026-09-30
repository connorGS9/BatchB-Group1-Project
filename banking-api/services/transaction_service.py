# services/transaction_service.py
# Business logic for transactions. A transfer coordinates two account balance
# changes and records a ledger entry. Depends on AccountService so balances and
# the accounts endpoints stay consistent.
from datetime import datetime
from typing import List, Optional
from datetime import date

from errors import ForbiddenError, ValidationError
from models.transaction import Transaction, TransactionType, TransferRequest
from repository.transaction_repository import TransactionRepository
from services.account_service import AccountService


class TransactionService:
    def __init__(self, repository: TransactionRepository, account_service: AccountService):
        self._repo = repository
        self._accounts = account_service

    def list_transactions(self, start_date: Optional[date] = None,
                          type: Optional[TransactionType] = None,
                          account_ids: Optional[List[int]] = None) -> List[Transaction]:
        """account_ids: only transactions touching these accounts (a customer's own)."""
        transactions = self._repo.list_all(start_date=start_date, type=type)
        if account_ids is not None:
            transactions = [t for t in transactions
                            if t.from_account_id in account_ids or t.to_account_id in account_ids]
        return transactions

    def transfer(self, data: TransferRequest,
                 acting_customer_id: Optional[int] = None) -> Transaction:
        """acting_customer_id = the logged-in customer. When given, they may only
        send money FROM their own account. Admins pass None (no limit)."""
        if data.amount <= 0:
            raise ValidationError("Transfer amount must be positive")
        if data.from_account_id == data.to_account_id:
            raise ValidationError("Cannot transfer to the same account")

        # Both must exist (raises NotFoundError) and be active with funds.
        source = self._accounts.get_account(data.from_account_id)
        target = self._accounts.get_account(data.to_account_id)
        if acting_customer_id is not None and source.customer_id != acting_customer_id:
            raise ForbiddenError("You can only send money from your own account")
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
