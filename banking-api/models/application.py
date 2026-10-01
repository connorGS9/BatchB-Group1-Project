from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints

# Reuse the customer field rules so an application validates names/email/phone the
# same way the customer record will once it's approved.
from models.customer import Email, Name, Phone

Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
# Usernames: letters, digits, underscore; 3-30 chars. Keeps login names tidy and
# avoids anything that could confuse the token/URL handling later.
Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=30,
                                            pattern=r"^[A-Za-z0-9_]+$")]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


class ApplicationCreate(BaseModel):
    """What a prospective customer submits on the public /apply form. The password
    is never stored as-is: the service hashes it (salt + PBKDF2) before saving."""
    first_name: Name
    last_name: Name
    email: Email
    phone: Phone
    address: Address
    base_salary: float = Field(ge=0, description="Informational: helps the admin decide")
    branch_id: int
    username: Username
    password: Password

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Maria", "last_name": "Lopez",
                "email": "maria.lopez@example.com", "phone": "555-0170",
                "address": "42 Market St, New York, NY",
                "base_salary": 65000, "branch_id": 1,
                "username": "marial", "password": "changeme123",
            }
        }


class Application(BaseModel):
    """Full stored application. Holds the hashed password (salt + hash), never the
    raw one, so it can become a real login on approval."""
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    base_salary: float
    branch_id: int
    username: str
    salt: str
    password_hash: str
    status: str = ApplicationStatus.PENDING.value
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None       # admin username
    decision_note: Optional[str] = None    # e.g. reason for a decline
    customer_id: Optional[int] = None       # set on approval
    account_id: Optional[int] = None        # set on approval


class ApplicationPublic(BaseModel):
    """What the admin dashboard sees: everything EXCEPT the salt/password hash."""
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    base_salary: float
    branch_id: int
    username: str
    status: str
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_note: Optional[str] = None
    customer_id: Optional[int] = None
    account_id: Optional[int] = None


class ApproveRequest(BaseModel):
    """Admin's approve action. Opening balance is optional and defaults to $0."""
    opening_balance: float = Field(default=0.0, ge=0)


class DeclineRequest(BaseModel):
    """Admin's decline action, with an optional reason kept on the record."""
    note: Optional[str] = None
