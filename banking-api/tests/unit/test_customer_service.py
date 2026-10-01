# tests/unit/test_customer_service.py
# Unit tests for CustomerService against mongomock-backed repos, plus the two
# cross-entity consistency bugs (stale account name, no deactivation cascade).
import pytest

from errors import NotFoundError, ValidationError
from models.customer import CustomerCreate, CustomerUpdate


# --------------------------------------------------------------------------
# Spec behaviour — passes today
# --------------------------------------------------------------------------
def test_get_missing_customer_raises_not_found(customer_service):
    with pytest.raises(NotFoundError):
        customer_service.get_customer(999)


def test_create_customer_duplicate_email_rejected(customer_service):
    data = CustomerCreate(first_name="New", last_name="Person",
                          email="john.doe@example.com", phone="555-9999")
    with pytest.raises(ValidationError):
        customer_service.create_customer(data)


def test_update_customer_to_existing_email_rejected(customer_service):
    with pytest.raises(ValidationError):
        customer_service.update_customer(2, CustomerUpdate(email="john.doe@example.com"))


# --------------------------------------------------------------------------
# BUG #7 — accounts copy the customer's first/last name, so renaming a customer
# leaves their account name stale.
# FIXED #7: update_customer() now copies any name change onto the customer's
# accounts, so their stored names stay in sync. Changed CustomerService (it now
# takes an account repository) in services/customer_service.py; wired in
# dependencies.py.
# --------------------------------------------------------------------------
def test_customer_rename_propagates_to_account(customer_service, account_repo):
    customer_service.update_customer(1, CustomerUpdate(first_name="Jonathan"))
    # Account #1 belongs to customer #1; its name should reflect the rename.
    assert account_repo.get(1).first_name == "Jonathan"


# --------------------------------------------------------------------------
# BUG #8 — deactivating a customer does NOT deactivate their accounts, so an
# inactive customer keeps active accounts that can still move money.
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="BUG #8: deactivating a customer leaves their accounts active",
                   strict=True)
def test_deactivating_customer_deactivates_their_accounts(customer_service, account_repo):
    customer_service.deactivate_customer(1)
    assert account_repo.get(1).is_active is False
