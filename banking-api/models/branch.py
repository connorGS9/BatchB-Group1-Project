from typing import Optional

from pydantic import BaseModel


class BranchCreate(BaseModel):
    """Fields a client supplies when creating a branch."""
    name: str
    city: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Downtown Branch",
                "city": "New York",
            }
        }


class BranchUpdate(BaseModel):
    """Fields a client may update. All optional so partial updates work."""
    name: Optional[str] = None
    city: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "city": "Boston",
            }
        }


class Branch(BaseModel):
    """Full branch record returned by the API."""
    id: int
    name: str
    city: str
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Downtown Branch",
                "city": "New York",
                "is_active": True,
            }
        }
