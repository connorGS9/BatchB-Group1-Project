# tests/unit/test_account_service.py
# Unit tests for AccountService against mongomock-backed repositories (conftest.py).
import pytest

from errors import NotFoundError, ValidationError
from models.account import AccountCreate


# --------------------------------------------------------------------------
# Overdraft protection  (spec behaviour — passes today)
# --------------------------------------------------------------------------
def test_withdraw_less_than_balance_succeeds(account_service, account_repo):
    account_service.adjust_balance(1, -1000.0)        # 5000 -> 4000
    assert account_repo.get(1).balance == 4000.0


def test_withdraw_exact_balance_leaves_zero(account_service, account_repo):
    account_service.adjust_balance(1, -5000.0)        # 5000 -> 0
    assert account_repo.get(1).balance == 0.0


def test_overdraft_is_rejected_and_not_saved(account_service, account_repo):
    with pytest.raises(ValidationError):
        account_service.adjust_balance(1, -6000.0)    # would go negative
    assert account_repo.get(1).balance == 5000.0      # unchanged


def test_adjust_inactive_account_is_rejected(account_service):
    account_service.deactivate_account(1)
    with pytest.raises(ValidationError):
        account_service.adjust_balance(1, -10.0)


def test_adjust_missing_account_raises_not_found(account_service):
    with pytest.raises(NotFoundError):
        account_service.adjust_balance(999, -10.0)


# --------------------------------------------------------------------------
# create_account  (spec behaviour — passes today)
# --------------------------------------------------------------------------
def test_create_account_negative_balance_rejected(account_service):
    data = AccountCreate(customer_id=1, first_name="A", last_name="B",
                         balance=-1.0, branch_id=1)
    with pytest.raises(ValidationError):
        account_service.create_account(data)


def test_create_account_unknown_customer_rejected(account_service):
    data = AccountCreate(customer_id=999, first_name="A", last_name="B",
                         balance=0.0, branch_id=1)
    with pytest.raises(ValidationError):
        account_service.create_account(data)


# --------------------------------------------------------------------------
# BUG #8 — an account can be opened for an INACTIVE customer. create_account only
# checks the customer exists, not that they are active.
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="BUG #8: accounts can be opened for an inactive customer",
                   strict=True)
def test_cannot_open_account_for_inactive_customer(account_service, customer_repo):
    inactive = customer_repo.get(1).model_copy(update={"is_active": False})
    customer_repo.update(inactive)
    data = AccountCreate(customer_id=1, first_name="John", last_name="Doe",
                         balance=0.0, branch_id=1)
    with pytest.raises(ValidationError):
        account_service.create_account(data)


# --------------------------------------------------------------------------
# BUG #8 — an account can be opened against a branch that does not exist.
# AccountService never validates branch_id (it has no branch repository).
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="BUG #8: accounts can be opened for a nonexistent branch",
                   strict=True)
def test_cannot_open_account_for_nonexistent_branch(account_service):
    data = AccountCreate(customer_id=1, first_name="John", last_name="Doe",
                         balance=0.0, branch_id=999)
    with pytest.raises(ValidationError):
        account_service.create_account(data)


# --------------------------------------------------------------------------
# BUG #5 — money is stored as float, so repeated adjustments accumulate rounding
# error and a balance that should land on 0.00 does not.
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="BUG #5: float balances accumulate rounding error",
                   strict=True)
def test_float_balance_has_no_rounding_error(account_service, account_repo):
    acc = account_service.create_account(
        AccountCreate(customer_id=1, first_name="T", last_name="T",
                      balance=0.30, branch_id=1))
    for _ in range(3):
        account_service.adjust_balance(acc.id, -0.10)
    assert account_repo.get(acc.id).balance == 0.0
