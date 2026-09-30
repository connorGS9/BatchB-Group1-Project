# repository/analytics_repository.py
# Reports calculated by MongoDB itself using aggregation pipelines.
# A pipeline is a list of steps; each step takes the documents from the step
# before it: filter ($match) -> join ($lookup) -> group and add up ($group) -> sort.
from typing import List

from db import db


class AnalyticsRepository:
    def __init__(self, database=db):
        self._db = database

    def branch_monthly_volume(self) -> List[dict]:
        """Money sent per branch per month (a transfer counts for the sender's branch)."""
        pipeline = [
            # 1. join each transaction to the account it came from
            {"$lookup": {"from": "accounts", "localField": "from_account_id",
                         "foreignField": "id", "as": "account"}},
            {"$unwind": "$account"},
            # 2. group by branch + year + month, adding up the amounts
            {"$group": {
                "_id": {"branch_id": "$account.branch_id",
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"}},
                "total_amount": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
            }},
            # 3. add the branch name
            {"$lookup": {"from": "branches", "localField": "_id.branch_id",
                         "foreignField": "id", "as": "branch"}},
            {"$sort": {"_id.branch_id": 1, "_id.year": 1, "_id.month": 1}},
        ]
        return [
            {
                "branch_id": row["_id"]["branch_id"],
                "branch_name": row["branch"][0]["name"] if row["branch"] else None,
                "year": row["_id"]["year"],
                "month": row["_id"]["month"],
                "total_amount": round(row["total_amount"], 2),
                "transaction_count": row["transaction_count"],
            }
            for row in self._db["transactions"].aggregate(pipeline)
        ]

    def branch_balances(self) -> List[dict]:
        """Number of active accounts and total / average balance per branch."""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$branch_id",
                "account_count": {"$sum": 1},
                "total_balance": {"$sum": "$balance"},
                "average_balance": {"$avg": "$balance"},
            }},
            {"$lookup": {"from": "branches", "localField": "_id",
                         "foreignField": "id", "as": "branch"}},
            {"$sort": {"_id": 1}},
        ]
        return [
            {
                "branch_id": row["_id"],
                "branch_name": row["branch"][0]["name"] if row["branch"] else None,
                "account_count": row["account_count"],
                "total_balance": round(row["total_balance"], 2),
                "average_balance": round(row["average_balance"], 2),
            }
            for row in self._db["accounts"].aggregate(pipeline)
        ]
