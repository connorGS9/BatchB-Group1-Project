# controllers/auth_controller.py
# API layer for login: POST /login, GET /me, POST /logout.
# The frontend sends the token back in the header:  Authorization: Bearer <token>
from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import auth_service as service
from errors import AuthError, RateLimitError
from models.user import LoginRequest, LoginResponse, UserPublic
from security import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """Public. Right password -> a JWT. Wrong -> 401. Too many wrong -> 429."""
    try:
        return service.login(data.username, data.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))


@router.get("/me", response_model=UserPublic)
def me(user: UserPublic = Depends(get_current_user)):
    """Who does this token belong to? (401 if no/bad/expired token)"""
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: UserPublic = Depends(get_current_user)):
    """JWTs aren't stored on the server, so logging out = the browser deletes its
    token. The token also stops working by itself when it expires."""
    return None
