# services/application_service.py
# Business logic for account-opening applications: submit (public), then an admin
# approves or declines. Approval provisions the real customer, their first
# account, and a login, so the applicant can sign in right away.
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from errors import ConflictError, NotFoundError, ValidationError
from models.account import AccountCreate
from models.application import Application, ApplicationCreate, ApplicationStatus
from models.branch import Branch
from models.customer import CustomerCreate
from models.user import User
from security import CUSTOMER
from services.auth_service import hash_password


class ApplicationService:
    def __init__(self, repository, customer_service, account_service,
                 user_repository, customer_repository, branch_repository):
        self._repo = repository
        self._customer_service = customer_service      # create_customer on approval
        self._account_service = account_service        # create_account on approval
        self._users = user_repository                  # create the login on approval
        self._customers = customer_repository          # dup-email pre-check at submit
        self._branches = branch_repository             # validate branch / form options

    # ---------- public submit ----------
    def submit(self, data: ApplicationCreate) -> Application:
        # One open application per person: don't let someone stack several up.
        if self._repo.find_pending(data.email, data.username) is not None:
            raise ConflictError(
                "Your application is already in review — we'll be in touch. Check back soon.")
        # Already a real customer/login? Point them at sign-in instead.
        if self._users.find_by_username(data.username) is not None:
            raise ValidationError(
                "That username is taken. If you already bank with us, please sign in.")
        if self._customers.find_by_email(data.email) is not None:
            raise ValidationError(
                "An account already exists for that email. Please sign in instead.")
        # The chosen branch must exist and be open.
        branch = self._branches.get(data.branch_id)
        if branch is None or not branch.is_active:
            raise ValidationError(f"Branch {data.branch_id} does not exist or is not open.")

        salt = secrets.token_hex(16)
        application = Application(
            id=0,
            first_name=data.first_name, last_name=data.last_name,
            email=data.email, phone=data.phone, address=data.address,
            base_salary=data.base_salary, branch_id=data.branch_id,
            username=data.username,
            salt=salt, password_hash=hash_password(data.password, salt),
            status=ApplicationStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
        )
        return self._repo.add(application)

    # ---------- admin reads ----------
    def list_applications(self, status: Optional[str] = None) -> List[Application]:
        return self._repo.list_all(status)

    def get(self, app_id: int) -> Application:
        application = self._repo.get(app_id)
        if application is None:
            raise NotFoundError(f"Application {app_id} not found")
        return application

    def list_active_branches(self) -> List[Branch]:
        """Active branches only, for the public application form's dropdown."""
        return [b for b in self._branches.list_all() if b.is_active]

    # ---------- admin decisions ----------
    def approve(self, app_id: int, opening_balance: float, admin_username: str) -> Application:
        application = self.get(app_id)
        self._require_pending(application)

        # customer -> account -> login. If a later step fails it surfaces as an
        # error; true all-or-nothing atomicity is a known TODO for this project.
        customer = self._customer_service.create_customer(CustomerCreate(
            first_name=application.first_name, last_name=application.last_name,
            email=application.email, phone=application.phone, address=application.address))
        account = self._account_service.create_account(AccountCreate(
            customer_id=customer.id, first_name=application.first_name,
            last_name=application.last_name, balance=opening_balance,
            branch_id=application.branch_id))
        self._users.add(User(
            id=0, username=application.username,
            full_name=f"{application.first_name} {application.last_name}",
            role=CUSTOMER, customer_id=customer.id,
            salt=application.salt, password_hash=application.password_hash))

        application.status = ApplicationStatus.APPROVED.value
        application.decided_at = datetime.now(timezone.utc)
        application.decided_by = admin_username
        application.customer_id = customer.id
        application.account_id = account.id
        return self._repo.update(application)

    def decline(self, app_id: int, note: Optional[str], admin_username: str) -> Application:
        application = self.get(app_id)
        self._require_pending(application)
        application.status = ApplicationStatus.DECLINED.value
        application.decided_at = datetime.now(timezone.utc)
        application.decided_by = admin_username
        application.decision_note = note
        return self._repo.update(application)

    @staticmethod
    def _require_pending(application: Application) -> None:
        if application.status != ApplicationStatus.PENDING.value:
            raise ValidationError(
                f"Application {application.id} has already been {application.status.lower()}.")
