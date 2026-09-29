# repository/transaction_repository.py
# Data-access layer for the transaction ledger: in-memory store plus the raw
# date/type filtering. No HTTP, no business rules.
from datetime import date, datetime
from typing import List, Optional

from models.transaction import Transaction, TransactionType


class TransactionRepository:
    def __init__(self):
        # A couple of historical entries so date/type filtering has data to show.
        self._transactions: List[Transaction] = [
            Transaction(id=1, from_account_id=1, to_account_id=2, amount=100.0,
                        type=TransactionType.TRANSFER, timestamp=datetime(2026, 1, 15, 9, 30)),
            Transaction(id=2, from_account_id=3, to_account_id=4, amount=500.0,
                        type=TransactionType.TRANSFER, timestamp=datetime(2026, 2, 1, 14, 0)),
        ]
        self._next_id = 3

    def list_all(self, start_date: Optional[date] = None,
                 type: Optional[TransactionType] = None) -> List[Transaction]:
        results = self._transactions
        if start_date is not None:
            results = [t for t in results if t.timestamp.date() >= start_date]
        if type is not None:
            results = [t for t in results if t.type == type]
        return results

    def add(self, transaction: Transaction) -> Transaction:
        transaction.id = self._next_id
        self._next_id += 1
        self._transactions.append(transaction)
        return transaction
