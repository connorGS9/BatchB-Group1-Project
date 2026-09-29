from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    """Stored user record. Never returned by the API (it holds the password hash)."""
    id: int
    username: str
    full_name: str
    role: str  # "CUSTOMER" or "ADMIN"
    customer_id: Optional[int] = None
    salt: str
    password_hash: str


class UserPublic(BaseModel):
    """What the API returns about a user."""
    id: int
    username: str
    full_name: str
    role: str
    customer_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Fields the login form sends."""
    username: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john",
                "password": "password123",
            }
        }


class LoginResponse(BaseModel):
    """Returned after a successful login. The frontend keeps the token and sends it
    back as `Authorization: Bearer <token>`."""
    token: str
    user: UserPublic