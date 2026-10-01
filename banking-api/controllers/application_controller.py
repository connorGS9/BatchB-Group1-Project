# controllers/application_controller.py
# API layer for account-opening applications.
#   POST /applications            -> PUBLIC (rate-limited): a prospective customer applies
#   GET  /applications/branches   -> PUBLIC (rate-limited): active branches for the form
#   GET  /applications            -> admin: list (optionally ?status=PENDING)
#   POST /applications/{id}/approve  -> admin: provision customer + account + login
#   POST /applications/{id}/decline  -> admin: decline with an optional reason
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies import application_limiter, application_service as service, public_read_limiter
from errors import ConflictError, NotFoundError, RateLimitError, ValidationError
from models.application import (ApplicationCreate, ApplicationPublic, ApproveRequest,
                                DeclineRequest)
from models.branch import Branch
from models.user import UserPublic
from security import require_admin

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Behind nginx/Docker the browser's address is in
    X-Forwarded-For; fall back to the socket peer otherwise."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/", response_model=ApplicationPublic, status_code=status.HTTP_201_CREATED)
def submit_application(data: ApplicationCreate, request: Request):
    """Public. A prospective customer requests an account; an admin reviews it."""
    try:
        application_limiter.hit(
            _client_ip(request),
            "Too many applications from this device. Please try again later.")
        return service.submit(data)
    except RateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/branches", response_model=List[Branch])
def application_branches(request: Request):
    """Public. Active branches, so the application form can offer a real choice."""
    try:
        public_read_limiter.hit(_client_ip(request))
    except RateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    return service.list_active_branches()


@router.get("/", response_model=List[ApplicationPublic])
def list_applications(status: Optional[str] = Query(None, description="e.g. PENDING"),
                      _: UserPublic = Depends(require_admin)):
    return service.list_applications(status)


@router.post("/{app_id}/approve", response_model=ApplicationPublic)
def approve_application(app_id: int, body: ApproveRequest,
                        admin: UserPublic = Depends(require_admin)):
    try:
        return service.approve(app_id, body.opening_balance, admin.username)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{app_id}/decline", response_model=ApplicationPublic)
def decline_application(app_id: int, body: DeclineRequest,
                        admin: UserPublic = Depends(require_admin)):
    try:
        return service.decline(app_id, body.note, admin.username)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
