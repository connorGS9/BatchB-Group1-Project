from pymongo import MongoClient

from config import MONGO_DB, MONGO_URL

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client[MONGO_DB]