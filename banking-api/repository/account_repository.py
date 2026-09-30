# repository/account_repository.py
# Data-access layer for accounts, stored in the MongoDB "accounts" collection.
# The filters become a MongoDB query, e.g.
#   ?branch_id=1&min_balance=1000  ->  {"branch_id": 1, "balance": {"$gte": 1000}}
from typing import List, Optional

from db import db
from models.account import Account
from repository.counters import next_id


class AccountRepository:
    def __init__(self, database=db):
        self._db = database
        self._accounts = database["accounts"]

    def list_all(self, branch_id: Optional[int] = None,
                 min_balance: Optional[float] = None,
                 customer_id: Optional[int] = None) -> List[Account]:
        query = {}
        if branch_id is not None:
            query["branch_id"] = branch_id
        if min_balance is not None:
            query["balance"] = {"$gte": min_balance}
        if customer_id is not None:
            query["customer_id"] = customer_id
        return [Account(**doc) for doc in self._accounts.find(query, {"_id": 0}).sort("id", 1)]

    def get(self, account_id: int) -> Optional[Account]:
        doc = self._accounts.find_one({"id": account_id}, {"_id": 0})
        return Account(**doc) if doc else None

    def add(self, account: Account) -> Account:
        account.id = next_id("accounts", self._db)
        account.account_number = f"ACC{account.id:03d}"
        self._accounts.insert_one(account.model_dump())
        return account

    def update(self, account: Account) -> Account:
        self._accounts.update_one({"id": account.id}, {"$set": account.model_dump()})
        return account
