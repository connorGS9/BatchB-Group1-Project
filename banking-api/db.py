from pymongo import ASCENDING, DESCENDING, MongoClient

from config import MONGO_DB, MONGO_URL

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client[MONGO_DB]


def ensure_indexes(database=None):
    """Create the transaction history indexes if missing (a no-op when they exist).
    init-db.js only runs on an empty volume, so this brings older databases up to date."""
    database = database if database is not None else db
    transactions = database["transactions"]
    transactions.create_index([("from_account_id", ASCENDING), ("timestamp", DESCENDING)])
    transactions.create_index([("to_account_id", ASCENDING), ("timestamp", DESCENDING)])
