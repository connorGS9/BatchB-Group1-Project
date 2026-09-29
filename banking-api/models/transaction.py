from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransferRequest(BaseModel):
    """Client payload to move money between two accounts."""
    from_account_id: int
    to_account_id: int
    amount: float

    class Config:
        json_schema_extra = {
            "example": {
                "from_account_id": 1,
                "to_account_id": 2,
                "amount": 250.00,
            }
        }


class Transaction(BaseModel):
    """A recorded ledger entry."""
    id: int
    from_account_id: int
    to_account_id: int
    amount: float
    type: TransactionType
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "from_account_id": 1,
                "to_account_id": 2,
                "amount": 250.00,
                "type": "TRANSFER",
                "timestamp": "2026-09-29T12:00:00",
            }
        }
