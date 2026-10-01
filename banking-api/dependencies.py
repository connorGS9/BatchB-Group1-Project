# dependencies.py
# Composition root: build the shared repositories and services once, in one
# place, so every controller shares the same MongoDB-backed repositories. This is
# what lets a transfer (transaction layer) move money that the accounts
# endpoints then report.
from repository.account_repository import AccountRepository
from repository.analytics_repository import AnalyticsRepository
from repository.application_repository import ApplicationRepository
from repository.branch_repository import BranchRepository
from repository.customer_repository import CustomerRepository
from repository.transaction_repository import TransactionRepository
from repository.user_repository import UserRepository
from services.account_service import AccountService
from services.analytics_service import AnalyticsService
from services.application_service import ApplicationService
from services.auth_service import AuthService
from services.branch_service import BranchService
from services.customer_service import CustomerService
from services.transaction_service import TransactionService
from security import LoginRateLimiter, RateLimiter

# --- Shared repositories (built first so the services below can share them) ---
customer_repository = CustomerRepository()
account_repository = AccountRepository()
branch_repository = BranchRepository()

# --- Customers (shares the account repository so a rename/deactivate reaches the
#     customer's accounts, which keep a copy of the name) ---
customer_service = CustomerService(customer_repository, account_repository)

# --- Accounts (shares the customer and branch repositories to enforce the
#     customer link and reject unknown/closed branches) ---
account_service = AccountService(account_repository, customer_repository, branch_repository)

# --- Transactions (depends on the shared account_service) ---
transaction_repository = TransactionRepository()
transaction_service = TransactionService(transaction_repository, account_service)

# --- Branches ---
branch_service = BranchService(branch_repository)

# --- Login ---
user_repository = UserRepository()
login_limiter = LoginRateLimiter()   # 5 wrong passwords -> blocked for 5 minutes
auth_service = AuthService(user_repository, login_limiter)

# --- Account applications (public submit -> admin approve/decline) ---
application_repository = ApplicationRepository()
application_service = ApplicationService(
    application_repository, customer_service, account_service,
    user_repository, customer_repository, branch_repository)
# Public endpoints are the only unauthenticated routes, so they're rate-limited
# per client IP: a strict cap on submitting, a loose one on reading branches.
application_limiter = RateLimiter(max_hits=5, window_seconds=10 * 60)
public_read_limiter = RateLimiter(max_hits=60, window_seconds=5 * 60)

# --- Reports (MongoDB aggregation pipelines) ---
analytics_service = AnalyticsService(AnalyticsRepository())
