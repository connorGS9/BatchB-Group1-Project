# repository/transaction_repository.py
# Data-access layer for the transaction ledger, stored in the MongoDB
# "transactions" collection. Filters become a MongoDB query, e.g.
#   ?start_date=2026-01-01&type=TRANSFER
#   -> {"timestamp": {"$gte": 2026-01-01 00:00}, "type": "TRANSFER"}
from datetime import date, datetime, time
from typing import List, Optional

from db import db
from models.transaction import Transaction, TransactionType
from repository.counters import next_id


class TransactionRepository:
    def __init__(self, database=db):
        self._db = database
        self._transactions = database["transactions"]

    def list_all(self, start_date: Optional[date] = None,
                 type: Optional[TransactionType] = None) -> List[Transaction]:
        query = {}
        if start_date is not None:
            query["timestamp"] = {"$gte": datetime.combine(start_date, time.min)}
        if type is not None:
            query["type"] = type.value
        docs = self._transactions.find(query, {"_id": 0}).sort("timestamp", 1)
        return [Transaction(**doc) for doc in docs]

    def add(self, transaction: Transaction) -> Transaction:
        transaction.id = next_id("transactions", self._db)
        doc = transaction.model_dump()
        doc["type"] = transaction.type.value  # store the enum as plain text
        self._transactions.insert_one(doc)
        return transaction
