# tests/unit/test_repositories.py
# Repository-layer tests against an in-memory mongomock database (see conftest.py).
# These prove the query filters and the id counter behave, and pin down the
# "stale copy overwrites a newer balance" bug and the dead, non-atomic
# customer next_id().
from datetime import date

import pytest

from models.transaction import TransactionType
from repository.counters import next_id


# --------------------------------------------------------------------------
# Account filters  (spec behaviour — these pass today)
# --------------------------------------------------------------------------
def test_list_all_filters_by_branch(account_repo):
    assert [a.id for a in account_repo.list_all(branch_id=1)] == [1, 2]


def test_list_all_filters_by_min_balance(account_repo):
    # balance >= 10000 keeps Jane (15000) and Alice (20000)
    assert [a.id for a in account_repo.list_all(min_balance=10000)] == [2, 4]


def test_list_all_filters_by_customer(account_repo):
    assert [a.id for a in account_repo.list_all(customer_id=3)] == [3]


def test_list_all_combines_filters(account_repo):
    # branch 1 AND balance >= 10000  ->  only Jane's account
    assert [a.id for a in account_repo.list_all(branch_id=1, min_balance=10000)] == [2]


# --------------------------------------------------------------------------
# Transaction filters  (spec behaviour — these pass today)
# --------------------------------------------------------------------------
def test_transactions_filter_by_start_date(transaction_repo):
    # Seed has 2026-01-15 and 2026-02-01; on/after 2026-01-20 keeps only the later one.
    result = transaction_repo.list_all(start_date=date(2026, 1, 20))
    assert [t.id for t in result] == [2]


def test_transactions_filter_by_type(transaction_repo):
    result = transaction_repo.list_all(type=TransactionType.TRANSFER)
    assert [t.id for t in result] == [1, 2]


# --------------------------------------------------------------------------
# Counter  (spec behaviour — the atomic one used in production)
# --------------------------------------------------------------------------
def test_next_id_increments_sequentially(fake_db):
    assert next_id("accounts", fake_db) == 6
    assert next_id("accounts", fake_db) == 7


# --------------------------------------------------------------------------
# BUG #3 — AccountRepository.update() does $set on the WHOLE document, so saving
# a stale copy silently clobbers a balance that changed in the meantime.
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="BUG #3: update() $set of the whole doc overwrites a newer balance",
                   strict=True)
def test_stale_update_must_not_clobber_newer_balance(account_repo):
    stale = account_repo.get(2)                       # read balance 15000
    # A concurrent deposit lands and is persisted: balance is now 16000.
    account_repo.update(account_repo.get(2).model_copy(update={"balance": 16000.0}))
    # The holder of the stale copy saves an unrelated change (a rename).
    account_repo.update(stale.model_copy(update={"first_name": "Renamed"}))
    # The deposit must survive. Today it is overwritten back to 15000.
    assert account_repo.get(2).balance == 16000.0


# --------------------------------------------------------------------------
# BUG #9 — CustomerRepository.next_id() reads seq and adds 1 without $inc, so it
# is not atomic and hands out the SAME id twice. It is also unused (add() uses
# the atomic counters.next_id instead).
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="BUG #9: customer_repository.next_id() is non-atomic and returns duplicates",
                   strict=True)
def test_customer_repo_next_id_is_unique(customer_repo):
    assert customer_repo.next_id() != customer_repo.next_id()
