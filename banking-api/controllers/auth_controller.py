# controllers/auth_controller.py
# API layer for login: POST /login, GET /me, POST /logout.
# The frontend sends the token back in the header:  Authorization: Bearer <token>
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status

from dependencies import auth_service as service
from errors import AuthError
from models.user import LoginRequest, LoginResponse, UserPublic

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _token(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return None


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    try:
        return service.login(data.username, data.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserPublic)
def me(authorization: Optional[str] = Header(None)):
    try:
        return service.current_user(_token(authorization))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(authorization: Optional[str] = Header(None)):
    service.logout(_token(authorization))