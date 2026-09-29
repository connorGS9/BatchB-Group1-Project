from typing import Optional

from pydantic import BaseModel


class CustomerCreate(BaseModel):
    """Fields a client supplies when creating a customer."""
    first_name: str
    last_name: str
    email: str
    phone: str

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "555-0100",
            }
        }


class CustomerUpdate(BaseModel):
    """Fields a client may update. All optional so partial updates work."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "phone": "555-0199",
            }
        }


class Customer(BaseModel):
    """Full customer record returned by the API."""
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "555-0100",
                "is_active": True,
            }
        }
