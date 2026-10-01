// mongo-init/init-db.js
// Creates the "banking" database the FIRST time the MongoDB container starts
// (when the mongo-data volume is empty). Docker runs every .js file in
// /docker-entrypoint-initdb.d automatically; compose.yaml mounts this folder there.
//
// To run it again from scratch:  docker compose down -v   then   docker compose up

const bank = db.getSiblingDB("banking");

// ---------- Login: users ----------
// Passwords are never stored in plain text: each user has a random salt and a
// PBKDF2-SHA256 hash of (password + salt), 100,000 rounds.
//   john  / password123  -> customer #1 (John Doe)
//   admin / admin123     -> admin
bank.createCollection("users");
bank.users.createIndex({ username: 1 }, { unique: true });
bank.users.createIndex({ id: 1 }, { unique: true });
bank.users.insertMany([
  {
    id: 1, username: "john", full_name: "John Doe", role: "CUSTOMER", customer_id: 1,
    salt: "85c5d1c480ef3ab5295d33f6f03b1fe1",
    password_hash: "bbb3cf4f28ef6b73c9cd407e8bf5b61d0e2f35ce5f5171442415cfa78495624a",
  },
  {
    id: 2, username: "admin", full_name: "Bank Admin", role: "ADMIN", customer_id: null,
    salt: "5e44222c345264b12914bf0c0c156b33",
    password_hash: "4c71f3e855013c727b182f1e92711fbbd035bfc539d2b001c641778b96cc5b5d",
  },
]);

// ---------- Branches ----------
bank.createCollection("branches");
bank.branches.createIndex({ id: 1 }, { unique: true });
bank.branches.insertMany([
  { id: 1, name: "Downtown Branch", city: "New York", is_active: true },
  { id: 2, name: "Uptown Branch", city: "Boston", is_active: true },
  { id: 3, name: "Westside Branch", city: "Chicago", is_active: true },
]);

// ---------- Customers ----------
bank.createCollection("customers");
bank.customers.createIndex({ id: 1 }, { unique: true });
bank.customers.createIndex({ email: 1 }, { unique: true });
bank.customers.insertMany([
  { id: 1, first_name: "John", last_name: "Doe", email: "john.doe@example.com", phone: "555-0100", is_active: true },
  { id: 2, first_name: "Jane", last_name: "Smith", email: "jane.smith@example.com", phone: "555-0101", is_active: true },
  { id: 3, first_name: "Bob", last_name: "Johnson", email: "bob.johnson@example.com", phone: "555-0102", is_active: true },
  { id: 4, first_name: "Alice", last_name: "Brown", email: "alice.brown@example.com", phone: "555-0103", is_active: true },
  { id: 5, first_name: "Charlie", last_name: "Wilson", email: "charlie.wilson@example.com", phone: "555-0104", is_active: true },
]);

// ---------- Accounts ----------
bank.createCollection("accounts");
bank.accounts.createIndex({ id: 1 }, { unique: true });
bank.accounts.createIndex({ account_number: 1 }, { unique: true });
bank.accounts.createIndex({ branch_id: 1, balance: -1 }); // ?branch_id=&min_balance= filter
bank.accounts.createIndex({ customer_id: 1 });
bank.accounts.insertMany([
  { id: 1, account_number: "ACC001", customer_id: 1, first_name: "John", last_name: "Doe", balance: 5000.0, branch_id: 1, is_active: true },
  { id: 2, account_number: "ACC002", customer_id: 2, first_name: "Jane", last_name: "Smith", balance: 15000.0, branch_id: 1, is_active: true },
  { id: 3, account_number: "ACC003", customer_id: 3, first_name: "Bob", last_name: "Johnson", balance: 7500.0, branch_id: 2, is_active: true },
  { id: 4, account_number: "ACC004", customer_id: 4, first_name: "Alice", last_name: "Brown", balance: 20000.0, branch_id: 2, is_active: true },
  { id: 5, account_number: "ACC005", customer_id: 5, first_name: "Charlie", last_name: "Wilson", balance: 3200.0, branch_id: 3, is_active: true },
]);

// ---------- Transactions ----------
bank.createCollection("transactions");
bank.transactions.createIndex({ id: 1 }, { unique: true });
bank.transactions.createIndex({ timestamp: -1 }); // ?start_date= filter, newest first
bank.transactions.createIndex({ type: 1 });
// A customer's history = $or on from/to account, newest first. Compound with
// timestamp so the date filter and sort are served by the index too.
bank.transactions.createIndex({ from_account_id: 1, timestamp: -1 });
bank.transactions.createIndex({ to_account_id: 1, timestamp: -1 });
bank.transactions.insertMany([
  { id: 1, from_account_id: 1, to_account_id: 2, amount: 100.0, type: "TRANSFER", timestamp: new Date("2026-01-15T09:30:00Z") },
  { id: 2, from_account_id: 3, to_account_id: 4, amount: 500.0, type: "TRANSFER", timestamp: new Date("2026-02-01T14:00:00Z") },
]);

// ---------- Account applications ----------
// A prospective customer submits one of these from the public /apply page; an
// admin approves (which provisions a customer + account + login) or declines it.
bank.createCollection("applications");
bank.applications.createIndex({ id: 1 }, { unique: true });
bank.applications.createIndex({ status: 1 });
// At most one PENDING application per email, so near-simultaneous submits can't
// both create a duplicate. Declined/approved rows don't count toward this.
bank.applications.createIndex(
  { email: 1 },
  { unique: true, partialFilterExpression: { status: "PENDING" } }
);

// ---------- Counters ----------
// Next id for each collection (like auto-increment in SQL). Starts at the last seeded id.
// "users" is here so approvals can mint new logins without colliding with the two
// seeded users; "applications" starts at 0 (none seeded).
bank.createCollection("counters");
bank.counters.insertMany([
  { _id: "users", seq: 2 },
  { _id: "branches", seq: 3 },
  { _id: "customers", seq: 5 },
  { _id: "accounts", seq: 5 },
  { _id: "transactions", seq: 2 },
  { _id: "applications", seq: 0 },
]);

print(
  "banking database initialised:",
  "users =", bank.users.countDocuments(),
  ", customers =", bank.customers.countDocuments(),
  ", accounts =", bank.accounts.countDocuments(),
  ", branches =", bank.branches.countDocuments(),
  ", transactions =", bank.transactions.countDocuments()
);
