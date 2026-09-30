# tests/unit/test_account_service.py
# Unit tests for AccountService, with the repositories mocked (see conftest.py).
# Mock(spec=AccountRepository) is a fake repository: same methods as the real one,
# but it returns whatever we tell it and never touches MongoDB.
import pytest

from errors import NotFoundError, ValidationError
from models.account import AccountCreate


@pytest.fixture(autouse=True)
def save_returns_what_it_was_given(account_repo):
    """Make the fake repo's update()/add() hand back the account, like the real one."""
    account_repo.update.side_effect = lambda account: account
    account_repo.add.side_effect = lambda account: account.model_copy(
        update={"id": 6, "account_number": "ACC006"})


# ---------- Overdraft protection (AccountService.adjust_balance) ----------

def test_withdrawing_less_than_balance_succeeds(account_service, account_repo, make_account):
    account_repo.get.return_value = make_account(balance=100.0)

    updated = account_service.adjust_balance(1, -40.0)

    assert updated.balance == 60.0
    account_repo.update.assert_called_once()  # new balance was saved


def test_withdrawing_exactly_the_balance_leaves_zero(account_service, account_repo, make_account):
    account_repo.get.return_value = make_account(balance=100.0)

    updated = account_service.adjust_balance(1, -100.0)

    assert updated.balance == 0.0


def test_withdrawing_more_than_balance_is_rejected(account_service, account_repo, make_account):
    account_repo.get.return_value = make_account(balance=100.0)

    with pytest.raises(ValidationError, match="Insufficient funds"):
        account_service.adjust_balance(1, -150.0)

    account_repo.update.assert_not_called()  # overdraft was NOT saved


def test_adjusting_an_inactive_account_is_rejected(account_service, account_repo, make_account):
    account_repo.get.return_value = make_account(is_active=False)

    with pytest.raises(ValidationError, match="inactive"):
        account_service.adjust_balance(1, 10.0)

    account_repo.update.assert_not_called()


def test_adjusting_a_missing_account_is_not_found(account_service, account_repo):
    account_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        account_service.adjust_balance(999, 10.0)


# ---------- create_account ----------

def test_negative_opening_balance_is_rejected(account_service, account_repo):
    data = AccountCreate(customer_id=1, first_name="A", last_name="B", balance=-5.0, branch_id=1)

    with pytest.raises(ValidationError, match="negative"):
        account_service.create_account(data)

    account_repo.add.assert_not_called()


def test_unknown_customer_is_rejected(account_service, account_repo, customer_repo):
    customer_repo.get.return_value = None  # customer 42 doesn't exist
    data = AccountCreate(customer_id=42, first_name="A", last_name="B", balance=10.0, branch_id=1)

    with pytest.raises(ValidationError, match="Customer 42 does not exist"):
        account_service.create_account(data)

    account_repo.add.assert_not_called()


def test_account_opens_for_a_real_customer(account_service, account_repo, customer_repo):
    customer_repo.get.return_value = object()  # any customer found
    data = AccountCreate(customer_id=1, first_name="A", last_name="B", balance=10.0, branch_id=1)

    account = account_service.create_account(data)

    assert account.account_number == "ACC006"
    assert account.is_active is True
    account_repo.add.assert_called_once()


# ---------- Delete = deactivate ----------

def test_delete_deactivates_instead_of_removing(account_service, account_repo, make_account):
    account_repo.get.return_value = make_account(is_active=True)

    account = account_service.deactivate_account(1)

    assert account.is_active is False
