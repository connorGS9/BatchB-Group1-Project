# tests/unit/test_transaction_service.py
# Unit tests for TransactionService.transfer against mongomock-backed repos.
import pytest

from errors import NotFoundError, ValidationError
from models.transaction import TransactionType, TransferRequest


def _transfer(from_id, to_id, amount):
    return TransferRequest(from_account_id=from_id, to_account_id=to_id, amount=amount)


# --------------------------------------------------------------------------
# Successful transfer  (spec behaviour — passes today)
# --------------------------------------------------------------------------
def test_transfer_moves_money_and_records_ledger(transaction_service, account_repo,
                                                 transaction_repo):
    txn = transaction_service.transfer(_transfer(1, 2, 100.0))
    assert account_repo.get(1).balance == 4900.0      # 5000 - 100
    assert account_repo.get(2).balance == 15100.0     # 15000 + 100
    assert txn.type == TransactionType.TRANSFER
    # A ledger entry was appended (seed had 2).
    assert len(transaction_repo.list_all(type=TransactionType.TRANSFER)) == 3


# --------------------------------------------------------------------------
# Failure scenarios  (spec behaviour — each must raise and move no money)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("amount", [-5.0, 0.0])
def test_transfer_non_positive_amount_rejected(transaction_service, account_repo, amount):
    with pytest.raises(ValidationError):
        transaction_service.transfer(_transfer(1, 2, amount))
    assert account_repo.get(1).balance == 5000.0
    assert account_repo.get(2).balance == 15000.0


def test_transfer_insufficient_funds_rejected(transaction_service, account_repo):
    with pytest.raises(ValidationError):
        transaction_service.transfer(_transfer(1, 2, 999999.0))
    assert account_repo.get(1).balance == 5000.0
    assert account_repo.get(2).balance == 15000.0


def test_transfer_to_same_account_rejected(transaction_service):
    with pytest.raises(ValidationError):
        transaction_service.transfer(_transfer(1, 1, 50.0))


def test_transfer_from_inactive_account_rejected(transaction_service, account_service):
    account_service.deactivate_account(1)
    with pytest.raises(ValidationError):
        transaction_service.transfer(_transfer(1, 2, 50.0))


def test_transfer_to_inactive_account_rejected(transaction_service, account_service):
    account_service.deactivate_account(2)
    with pytest.raises(ValidationError):
        transaction_service.transfer(_transfer(1, 2, 50.0))


def test_transfer_from_missing_account_raises_not_found(transaction_service):
    with pytest.raises(NotFoundError):
        transaction_service.transfer(_transfer(999, 2, 50.0))


def test_transfer_to_missing_account_raises_not_found(transaction_service):
    with pytest.raises(NotFoundError):
        transaction_service.transfer(_transfer(1, 999, 50.0))


# --------------------------------------------------------------------------
# BUG #4 — a transfer is two separate writes (debit, then credit) with no
# atomicity. If the credit fails, the debit is already persisted and the money
# has vanished. We simulate the mid-transfer crash by making the second balance
# write raise. (mongomock cannot exercise a real Mongo transaction; a real-Mongo
# integration test is proposed for that.)
# FIXED #4: transfer() now debits the sender, then wraps the credit (and the
# ledger write) in try/except; if either fails it undoes what already happened
# (refunds the sender, and reverses the receiver too if the ledger failed) and
# re-raises, so no money is lost or created. Changed TransactionService.transfer in
# services/transaction_service.py.
# --------------------------------------------------------------------------
def test_failed_transfer_does_not_lose_money(transaction_service, account_service,
                                             account_repo, monkeypatch):
    real_adjust = account_service.adjust_balance
    calls = {"n": 0}

    def flaky_adjust(account_id, delta):
        calls["n"] += 1
        if calls["n"] == 2:                           # the credit leg
            raise RuntimeError("crash between debit and credit")
        return real_adjust(account_id, delta)

    monkeypatch.setattr(account_service, "adjust_balance", flaky_adjust)

    with pytest.raises(RuntimeError):
        transaction_service.transfer(_transfer(1, 2, 100.0))

    # The sender must not have lost money to a transfer that never completed.
    assert account_repo.get(1).balance == 5000.0
