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

// ---------- Login: sessions ----------
// One document per signed-in browser: { token, user_id, created_at }.
// Login creates one, logout deletes it. Sessions older than 1 day are removed
// automatically by the TTL index.
bank.createCollection("sessions");
bank.sessions.createIndex({ token: 1 }, { unique: true });
bank.sessions.createIndex({ created_at: 1 }, { expireAfterSeconds: 86400 });

print("banking database initialised: users =", bank.users.countDocuments(), ", sessions collection ready");