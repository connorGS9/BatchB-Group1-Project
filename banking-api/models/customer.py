from typing import Annotated, Optional

from pydantic import BaseModel, StringConstraints

# Input validation (Chapter 4): reject junk before it reaches the database.
# Bad input -> FastAPI answers 422 with a message saying which field is wrong.
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Email = Annotated[str, StringConstraints(strip_whitespace=True, max_length=254,
                                         pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9+()\-.\s]{7,20}$")]


class CustomerCreate(BaseModel):
    """Fields a client supplies when creating a customer."""
    first_name: Name
    last_name: Name
    email: Email
    phone: Phone

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
    first_name: Optional[Name] = None
    last_name: Optional[Name] = None
    email: Optional[Email] = None
    phone: Optional[Phone] = None

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
