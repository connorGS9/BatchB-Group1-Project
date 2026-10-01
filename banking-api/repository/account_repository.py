# repository/account_repository.py
# Data-access layer for accounts, stored in the MongoDB "accounts" collection.
# The filters become a MongoDB query, e.g.
#   ?branch_id=1&min_balance=1000  ->  {"branch_id": 1, "balance": {"$gte": 1000}}
from typing import List, Optional

from pymongo import ReturnDocument

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
        # Never write the balance here. update() saves a whole copy of the account,
        # which may be stale; writing its balance would silently overwrite a change
        # the atomic path made in the meantime (BUG #3). Balance is owned solely by
        # adjust_balance() below.
        changes = account.model_dump()
        changes.pop("balance", None)
        self._accounts.update_one({"id": account.id}, {"$set": changes})
        return account

    def adjust_balance(self, account_id: int, delta: float) -> Optional[Account]:
        """Atomically add `delta` to an account's balance in ONE database operation.
        The money only moves if the account is active and (for a withdrawal) still
        has enough funds, so two overlapping changes can never lose or clobber each
        other. Returns the updated account, or None if the guard was not met
        (missing/inactive account, or insufficient funds)."""
        query = {"id": account_id, "is_active": True}
        if delta < 0:
            query["balance"] = {"$gte": -delta}
        doc = self._accounts.find_one_and_update(
            query,
            {"$inc": {"balance": delta}},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            return None
        doc.pop("_id", None)
        return Account(**doc)
