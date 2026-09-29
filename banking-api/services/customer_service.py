# services/customer_service.py
# Business/domain logic. Coordinates the repository and enforces rules,
# raising NotFoundError / ValidationError for the controller to translate.
from typing import List

from errors import NotFoundError, ValidationError
from models.customer import Customer, CustomerCreate, CustomerUpdate
from repository.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository = None):
        self._repo = repository or CustomerRepository()

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
        return self._repo.update(updated)

    def deactivate_customer(self, customer_id: int) -> Customer:
        """DELETE = deactivate: soft-delete by flipping is_active to False."""
        customer = self.get_customer(customer_id)
        updated = customer.model_copy(update={"is_active": False})
        return self._repo.update(updated)
