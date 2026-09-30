# tests/unit/test_transaction_service.py
# Unit tests for TransactionService.transfer, with the repositories mocked (see conftest.py).
# The fake account repo reads/writes a plain dict, so we can check exactly which
# balances changed, and that a failed transfer changes NOTHING.
import pytest

from errors import NotFoundError, ValidationError
from models.transaction import TransactionType, TransferRequest


@pytest.fixture
def accounts(make_account):
    """Our pretend 'database' of accounts."""
    return {
        1: make_account(id=1, account_number="ACC001", balance=500.0),
        2: make_account(id=2, account_number="ACC002", customer_id=2, balance=100.0),
        3: make_account(id=3, account_number="ACC003", customer_id=3, balance=900.0, is_active=False),
    }


@pytest.fixture(autouse=True)
def fake_database(accounts, account_repo, transaction_repo):
    """Wire the mocked repositories to the dict above."""
    account_repo.get.side_effect = lambda account_id: accounts.get(account_id)

    def save(account):
        accounts[account.id] = account
        return account

    account_repo.update.side_effect = save
    transaction_repo.add.side_effect = lambda t: t.model_copy(update={"id": 3})


def transfer(from_id, to_id, amount):
    return TransferRequest(from_account_id=from_id, to_account_id=to_id, amount=amount)


@pytest.fixture
def assert_nothing_changed(accounts, account_repo, transaction_repo):
    def check():
        assert accounts[1].balance == 500.0
        assert accounts[2].balance == 100.0
        assert accounts[3].balance == 900.0
        account_repo.update.assert_not_called()   # no balance saved
        transaction_repo.add.assert_not_called()  # no transaction recorded
    return check


# ---------- Failure scenarios: each must raise and leave balances untouched ----------

def test_insufficient_funds(transaction_service, assert_nothing_changed):
    with pytest.raises(ValidationError, match="Insufficient funds"):
        transaction_service.transfer(transfer(1, 2, 10_000.0))
    assert_nothing_changed()


def test_negative_amount(transaction_service, assert_nothing_changed):
    with pytest.raises(ValidationError, match="must be positive"):
        transaction_service.transfer(transfer(1, 2, -50.0))
    assert_nothing_changed()


def test_zero_amount(transaction_service, assert_nothing_changed):
    with pytest.raises(ValidationError, match="must be positive"):
        transaction_service.transfer(transfer(1, 2, 0.0))
    assert_nothing_changed()


def test_same_source_and_target(transaction_service, assert_nothing_changed):
    with pytest.raises(ValidationError, match="same account"):
        transaction_service.transfer(transfer(1, 1, 50.0))
    assert_nothing_changed()


def test_source_account_inactive(transaction_service, assert_nothing_changed):
    with pytest.raises(ValidationError, match="inactive"):
        transaction_service.transfer(transfer(3, 2, 50.0))
    assert_nothing_changed()


def test_target_account_inactive(transaction_service, assert_nothing_changed):
    # Sender must NOT be charged when the receiver is closed.
    with pytest.raises(ValidationError, match="inactive"):
        transaction_service.transfer(transfer(1, 3, 50.0))
    assert_nothing_changed()


def test_source_account_missing(transaction_service, assert_nothing_changed):
    with pytest.raises(NotFoundError):
        transaction_service.transfer(transfer(999, 2, 50.0))
    assert_nothing_changed()


def test_target_account_missing(transaction_service, assert_nothing_changed):
    with pytest.raises(NotFoundError):
        transaction_service.transfer(transfer(1, 999, 50.0))
    assert_nothing_changed()


# ---------- Successful transfer ----------

def test_successful_transfer(transaction_service, accounts, transaction_repo):
    result = transaction_service.transfer(transfer(1, 2, 200.0))

    assert accounts[1].balance == 300.0   # source debited: 500 - 200
    assert accounts[2].balance == 300.0   # target credited: 100 + 200
    transaction_repo.add.assert_called_once()  # a transaction was recorded
    assert result.type == TransactionType.TRANSFER
    assert result.amount == 200.0
    assert (result.from_account_id, result.to_account_id) == (1, 2)
