# dependencies.py
# Composition root: build the shared repositories and services once, in one
# place, so every controller shares the same MongoDB-backed repositories. This is
# what lets a transfer (transaction layer) move money that the accounts
# endpoints then report.
from repository.account_repository import AccountRepository
from repository.analytics_repository import AnalyticsRepository
from repository.branch_repository import BranchRepository
from repository.customer_repository import CustomerRepository
from repository.transaction_repository import TransactionRepository
from repository.user_repository import UserRepository
from services.account_service import AccountService
from services.analytics_service import AnalyticsService
from services.auth_service import AuthService
from services.branch_service import BranchService
from services.customer_service import CustomerService
from services.transaction_service import TransactionService
from security import LoginRateLimiter

# --- Customers (built first so accounts can validate customer_id against them) ---
customer_repository = CustomerRepository()
customer_service = CustomerService(customer_repository)

# --- Accounts (shares the customer repository to enforce the customer link) ---
account_repository = AccountRepository()
account_service = AccountService(account_repository, customer_repository)

# --- Transactions (depends on the shared account_service) ---
transaction_repository = TransactionRepository()
transaction_service = TransactionService(transaction_repository, account_service)

# --- Branches ---
branch_repository = BranchRepository()
branch_service = BranchService(branch_repository)

# --- Login ---
user_repository = UserRepository()
login_limiter = LoginRateLimiter()   # 5 wrong passwords -> blocked for 5 minutes
auth_service = AuthService(user_repository, login_limiter)

# --- Reports (MongoDB aggregation pipelines) ---
analytics_service = AnalyticsService(AnalyticsRepository())
