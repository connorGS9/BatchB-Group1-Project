# dependencies.py
# Composition root: build the shared repositories and services once, in one
# place, so every controller talks to the SAME in-memory store. This is what
# lets a transfer (transaction layer) actually move money that the accounts
# endpoints then report.
from repository.account_repository import AccountRepository
from repository.branch_repository import BranchRepository
from repository.customer_repository import CustomerRepository
from repository.transaction_repository import TransactionRepository
from repository.session_repository import SessionRepository
from repository.user_repository import UserRepository
from services.account_service import AccountService
from services.auth_service import AuthService
from services.branch_service import BranchService
from services.customer_service import CustomerService
from services.transaction_service import TransactionService

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
session_repository = SessionRepository()
auth_service = AuthService(user_repository, session_repository)