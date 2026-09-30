# repository/counters.py
# Hands out the next id for a collection (1, 2, 3, ...), like an auto-increment
# column in SQL. The "counters" collection keeps one document per collection:
#   { _id: "accounts", seq: 5 }
# $inc makes it atomic, so two requests at the same time never get the same id.
from pymongo import ReturnDocument

from db import db


def next_id(name: str, database=db) -> int:
    counter = database["counters"].find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return counter["seq"]
