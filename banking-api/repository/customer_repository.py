# repository/customer_repository.py
# Data-access layer for customers, stored in the MongoDB "customers" collection.
# Knows nothing about HTTP or business rules. Returns/accepts Customer models.
from typing import List, Optional

from db import db
from models.customer import Customer
from repository.counters import next_id


class CustomerRepository:
    def __init__(self, database=db):
        self._db = database
        self._customers = database["customers"]

    def list_all(self) -> List[Customer]:
        return [Customer(**doc) for doc in self._customers.find({}, {"_id": 0}).sort("id", 1)]

    def get(self, customer_id: int) -> Optional[Customer]:
        doc = self._customers.find_one({"id": customer_id}, {"_id": 0})
        return Customer(**doc) if doc else None

    def find_by_email(self, email: str) -> Optional[Customer]:
        doc = self._customers.find_one({"email": email}, {"_id": 0})
        return Customer(**doc) if doc else None

    def add(self, customer: Customer) -> Customer:
        customer.id = next_id("customers", self._db)
        self._customers.insert_one(customer.model_dump())
        return customer

    def update(self, customer: Customer) -> Customer:
        self._customers.update_one({"id": customer.id}, {"$set": customer.model_dump()})
        return customer

    def next_id(self) -> int:
        # Hand out the next customer id through the shared ATOMIC counter. The old
        # read-the-seq-then-add-1 was two separate steps, so two callers could read
        # the same seq and both return the same id. counters.next_id uses a single
        # atomic $inc, so every caller gets a different number.
        return next_id("customers", self._db)
