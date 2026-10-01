# services/customer_service.py
# Business/domain logic. Coordinates the repository and enforces rules,
# raising NotFoundError / ValidationError for the controller to translate.
from typing import List

from errors import NotFoundError, ValidationError
from models.customer import Customer, CustomerCreate, CustomerUpdate
from repository.account_repository import AccountRepository
from repository.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository = None,
                 account_repository: AccountRepository = None):
        self._repo = repository or CustomerRepository()
        # Accounts store a copy of the customer's name, so renaming or deactivating
        # a customer has to reach their accounts too.
        self._accounts = account_repository or AccountRepository()

    def list_customers(self) -> List[Customer]:
        return self._repo.list_all()

    def get_customer(self, customer_id: int) -> Customer:
        customer = self._repo.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return customer

    def create_customer(self, data: CustomerCreate) -> Customer:
        if self._repo.find_by_email(data.email) is not None:
            raise ValidationError(f"Email {data.email} is already in use")
        customer = Customer(id=0, is_active=True, **data.model_dump())
        return self._repo.add(customer)

    def update_customer(self, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = self.get_customer(customer_id)
        changes = data.model_dump(exclude_unset=True)

        new_email = changes.get("email")
        if new_email and new_email != customer.email:
            if self._repo.find_by_email(new_email) is not None:
                raise ValidationError(f"Email {new_email} is already in use")

        updated = customer.model_copy(update=changes)
        saved = self._repo.update(updated)

        # Accounts keep a copy of the name, so copy any name change onto them.
        if "first_name" in changes or "last_name" in changes:
            for account in self._accounts.list_all(customer_id=saved.id):
                renamed = account.model_copy(
                    update={"first_name": saved.first_name,
                            "last_name": saved.last_name})
                self._accounts.update(renamed)
        return saved

    def deactivate_customer(self, customer_id: int) -> Customer:
        """DELETE = deactivate: soft-delete by flipping is_active to False.
        Deactivating a customer also deactivates their accounts, so an inactive
        customer can't be left with active accounts that still move money."""
        customer = self.get_customer(customer_id)
        updated = customer.model_copy(update={"is_active": False})
        saved = self._repo.update(updated)

        for account in self._accounts.list_all(customer_id=customer_id):
            self._accounts.update(account.model_copy(update={"is_active": False}))
        return saved
