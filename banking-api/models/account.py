from typing import Optional

from pydantic import BaseModel


class AccountCreate(BaseModel):
    """Fields a client supplies when opening an account.
    id and account_number are assigned by the server.
    customer_id must reference an existing customer."""
    customer_id: int
    first_name: str
    last_name: str
    balance: float = 0.0
    branch_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "balance": 5000.00,
                "branch_id": 1,
            }
        }


class AccountUpdate(BaseModel):
    """Fields a client may update. All optional so partial updates work.
    Balance is intentionally excluded — it changes via transactions."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    branch_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "branch_id": 2,
            }
        }


class Account(BaseModel):
    """Full account record returned by the API."""
    id: int
    account_number: str
    customer_id: int
    first_name: str
    last_name: str
    balance: float
    branch_id: int
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "account_number": "ACC001",
                "customer_id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "balance": 5000.00,
                "branch_id": 1,
                "is_active": True,
            }
        }


class AccountPublic(BaseModel):
    """What any logged-in customer may see about ANOTHER account: enough to send
    money to it, but not its balance or owner id."""
    id: int
    account_number: str
    first_name: str
    last_name: str
    is_active: bool = True
