# repository/customer_repository.py
# Data-access layer: owns the in-memory store and knows nothing about HTTP
# or business rules. Returns/accepts Customer models; raises no domain errors.
from typing import List, Optional

from models.customer import Customer


class CustomerRepository:
    def __init__(self):
        self._customers: List[Customer] = [
            Customer(id=1, first_name="John", last_name="Doe",
                     email="john.doe@example.com", phone="555-0100"),
            Customer(id=2, first_name="Jane", last_name="Smith",
                     email="jane.smith@example.com", phone="555-0101"),
            Customer(id=3, first_name="Bob", last_name="Johnson",
                     email="bob.johnson@example.com", phone="555-0102"),
            Customer(id=4, first_name="Alice", last_name="Brown",
                     email="alice.brown@example.com", phone="555-0103"),
            Customer(id=5, first_name="Charlie", last_name="Wilson",
                     email="charlie.wilson@example.com", phone="555-0104"),
        ]
        self._next_id = 6

    def list_all(self) -> List[Customer]:
        return self._customers

    def get(self, customer_id: int) -> Optional[Customer]:
        return next((c for c in self._customers if c.id == customer_id), None)

    def find_by_email(self, email: str) -> Optional[Customer]:
        return next((c for c in self._customers if c.email == email), None)

    def add(self, customer: Customer) -> Customer:
        customer.id = self._next_id
        self._next_id += 1
        self._customers.append(customer)
        return customer

    def update(self, customer: Customer) -> Customer:
        for i, existing in enumerate(self._customers):
            if existing.id == customer.id:
                self._customers[i] = customer
                return customer
        return customer

    def next_id(self) -> int:
        return self._next_id
