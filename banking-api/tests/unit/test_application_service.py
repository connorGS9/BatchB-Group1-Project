# tests/unit/test_application_service.py
# Unit tests for ApplicationService (submit / approve / decline) and the shared
# RateLimiter, against the mongomock-backed repositories from conftest.py.
import pytest

from errors import ConflictError, RateLimitError, ValidationError
from models.application import ApplicationCreate, ApplicationStatus
from security import RateLimiter
from services.auth_service import hash_password


def _application(**overrides) -> ApplicationCreate:
    fields = dict(
        first_name="Maria", last_name="Lopez",
        email="maria.lopez@example.com", phone="555-0170",
        address="42 Market St", base_salary=65000.0, branch_id=1,
        username="marial", password="changeme123",
    )
    fields.update(overrides)
    return ApplicationCreate(**fields)


# --------------------------------------------------------------------------
# submit
# --------------------------------------------------------------------------
def test_submit_creates_pending_application_without_plaintext_password(application_service, application_repo):
    app = application_service.submit(_application())
    assert app.status == ApplicationStatus.PENDING.value
    assert app.id >= 1
    stored = application_repo.get(app.id)
    # Password is stored hashed (salt + PBKDF2), never as the raw string.
    assert stored.password_hash != "changeme123"
    assert stored.password_hash == hash_password("changeme123", stored.salt)


def test_submit_twice_same_email_is_conflict_and_makes_no_duplicate(application_service, application_repo):
    application_service.submit(_application())
    with pytest.raises(ConflictError):
        application_service.submit(_application(username="different"))  # same email, still PENDING
    assert len(application_repo.list_all(status="PENDING")) == 1


def test_submit_twice_same_username_is_conflict(application_service):
    application_service.submit(_application())
    with pytest.raises(ConflictError):
        application_service.submit(_application(email="other@example.com"))


def test_submit_existing_username_rejected(application_service):
    with pytest.raises(ValidationError):
        application_service.submit(_application(username="john"))  # seeded login


def test_submit_existing_customer_email_rejected(application_service):
    with pytest.raises(ValidationError):
        application_service.submit(_application(email="john.doe@example.com"))  # seeded customer


def test_submit_unknown_branch_rejected(application_service):
    with pytest.raises(ValidationError):
        application_service.submit(_application(branch_id=999))


# --------------------------------------------------------------------------
# approve
# --------------------------------------------------------------------------
def test_approve_provisions_customer_account_and_login(application_service, application_repo,
                                                        customer_repo, account_repo, user_repo):
    app = application_service.submit(_application())
    decided = application_service.approve(app.id, opening_balance=250.0, admin_username="admin")

    assert decided.status == ApplicationStatus.APPROVED.value
    assert decided.customer_id is not None and decided.account_id is not None
    assert decided.decided_by == "admin"

    customer = customer_repo.get(decided.customer_id)
    assert customer.email == "maria.lopez@example.com"
    assert customer.address == "42 Market St"

    account = account_repo.get(decided.account_id)
    assert account.balance == 250.0
    assert account.customer_id == customer.id
    assert account.branch_id == 1

    user = user_repo.find_by_username("marial")
    assert user is not None and user.role == "CUSTOMER" and user.customer_id == customer.id
    # The login works with the password chosen on the application.
    assert user.password_hash == hash_password("changeme123", user.salt)


def test_approve_defaults_to_zero_opening_balance(application_service, account_repo):
    app = application_service.submit(_application())
    decided = application_service.approve(app.id, opening_balance=0.0, admin_username="admin")
    assert account_repo.get(decided.account_id).balance == 0.0


def test_approve_already_decided_is_rejected(application_service):
    app = application_service.submit(_application())
    application_service.approve(app.id, 0.0, "admin")
    with pytest.raises(ValidationError):
        application_service.approve(app.id, 0.0, "admin")


# --------------------------------------------------------------------------
# decline
# --------------------------------------------------------------------------
def test_decline_marks_declined_and_creates_no_customer(application_service, application_repo, customer_repo):
    before = len(customer_repo.list_all())
    app = application_service.submit(_application())
    decided = application_service.decline(app.id, note="Insufficient history", admin_username="admin")
    assert decided.status == ApplicationStatus.DECLINED.value
    assert decided.decision_note == "Insufficient history"
    assert len(customer_repo.list_all()) == before  # nothing provisioned


def test_declined_email_can_apply_again(application_service):
    app = application_service.submit(_application())
    application_service.decline(app.id, note=None, admin_username="admin")
    # No longer PENDING, so the same person may re-apply.
    again = application_service.submit(_application())
    assert again.status == ApplicationStatus.PENDING.value


# --------------------------------------------------------------------------
# RateLimiter (generalized from LoginRateLimiter)
# --------------------------------------------------------------------------
def test_rate_limiter_allows_up_to_cap_then_blocks():
    now = [0.0]
    limiter = RateLimiter(max_hits=3, window_seconds=60, clock=lambda: now[0])
    for _ in range(3):
        limiter.hit("1.2.3.4")           # 3 allowed
    with pytest.raises(RateLimitError):
        limiter.hit("1.2.3.4")           # 4th blocked


def test_rate_limiter_window_expires():
    now = [0.0]
    limiter = RateLimiter(max_hits=1, window_seconds=60, clock=lambda: now[0])
    limiter.hit("1.2.3.4")
    now[0] = 61                           # window passed
    limiter.hit("1.2.3.4")               # allowed again, no raise


def test_rate_limiter_is_per_key():
    now = [0.0]
    limiter = RateLimiter(max_hits=1, window_seconds=60, clock=lambda: now[0])
    limiter.hit("1.1.1.1")
    limiter.hit("2.2.2.2")               # different key, independent budget
