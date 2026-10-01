// mongo-init/seed-demo-transactions.js
// Made-up transfer history for the last 60 days, so the customer dashboard
// (balance chart, money flow, recent recipients) has something to show.
// Docker runs /docker-entrypoint-initdb.d files in name order, so this runs right
// after init-db.js on a fresh volume.
//
// To add it to an existing database (safe to run twice; the second run does nothing):
//   docker exec bank-mongo sh -c 'mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" \
//     -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin \
//     /docker-entrypoint-initdb.d/seed-demo-transactions.js'
//
// Every transfer also moves the money between account balances, exactly like
// TransactionService.transfer(), so balances always match the ledger. Dates are
// relative to when the script runs.

const bank = db.getSiblingDB("banking");
const DAYS = 60;
const DAY_MS = 24 * 60 * 60 * 1000;
const now = Date.now();
const windowStart = new Date(now - DAYS * DAY_MS);

if (bank.transactions.countDocuments({ timestamp: { $gte: windowStart } }) > 0) {
  print("demo transactions: recent history already present, skipping");
  quit();
}

// Small deterministic random generator, so every fresh volume gets the same history.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}
const between = (lo, hi) => Math.round((lo + rand() * (hi - lo)) * 100) / 100;
const pick = (list) => list[Math.floor(rand() * list.length)];

// Account ids from init-db.js: 1 John, 2 Jane, 3 Bob, 4 Alice, 5 Charlie.
const balances = {};
bank.accounts.find({ is_active: true }).forEach((a) => { balances[a.id] = a.balance; });
const ids = Object.keys(balances).map(Number);

const planned = [];
for (let day = DAYS; day >= 1; day--) {
  const dayStart = now - day * DAY_MS;
  const at = () => new Date(dayStart + Math.floor(rand() * 12 + 8) * 60 * 60 * 1000);

  // John gets paid by Alice every two weeks, plus the odd refund/split from friends.
  if (day % 14 === 3) planned.push({ from: 4, to: 1, amount: between(1400, 1600), at: at() });
  if (rand() < 0.15) planned.push({ from: pick([2, 3, 5]), to: 1, amount: between(20, 180), at: at() });

  // John's everyday spending: rent-sized payment once a month, small payments most days.
  if (day % 30 === 25) planned.push({ from: 1, to: 2, amount: 1200, at: at() });
  const spends = rand() < 0.6 ? (rand() < 0.3 ? 2 : 1) : 0;
  for (let i = 0; i < spends; i++) planned.push({ from: 1, to: pick([2, 3, 5]), amount: between(12, 140), at: at() });

  // Background activity between the other customers.
  if (rand() < 0.5) {
    const from = pick(ids.filter((id) => id !== 1));
    const to = pick(ids.filter((id) => id !== from));
    planned.push({ from, to, amount: between(25, 600), at: at() });
  }
}
planned.sort((a, b) => a.at - b.at);

let nextId = bank.counters.findOne({ _id: "transactions" }).seq;
const docs = [];
for (const t of planned) {
  if (!(t.from in balances) || !(t.to in balances)) continue; // inactive account
  if (balances[t.from] < t.amount) continue;                  // insufficient funds, like the API
  balances[t.from] = Math.round((balances[t.from] - t.amount) * 100) / 100;
  balances[t.to] = Math.round((balances[t.to] + t.amount) * 100) / 100;
  docs.push({ id: ++nextId, from_account_id: t.from, to_account_id: t.to, amount: t.amount, type: "TRANSFER", timestamp: t.at });
}

bank.transactions.insertMany(docs);
for (const id of ids) bank.accounts.updateOne({ id }, { $set: { balance: balances[id] } });
bank.counters.updateOne({ _id: "transactions" }, { $set: { seq: nextId } });

print("demo transactions: inserted", docs.length, "; balances now", JSON.stringify(balances));
