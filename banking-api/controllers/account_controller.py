# controllers/account_controller.py
# API layer: maps HTTP requests to the service and domain errors to status codes.
# Access: admins -> everything. Customers -> see only their OWN accounts, plus a
# "directory" of account numbers + names (no balances) so they can send money.
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import account_service as service
from errors import NotFoundError, ValidationError
from models.account import Account, AccountCreate, AccountPublic, AccountUpdate
from models.user import UserPublic
from security import get_current_user, is_admin, require_admin

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("/", response_model=List[Account])
def list_accounts(
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    min_balance: Optional[float] = Query(None, description="Only accounts with balance >= this"),
    customer_id: Optional[int] = Query(None, description="Only accounts owned by this customer"),
    user: UserPublic = Depends(get_current_user),
):
    if not is_admin(user):
        customer_id = user.customer_id   # customers only ever see their own accounts
    return service.list_accounts(branch_id=branch_id, min_balance=min_balance,
                                 customer_id=customer_id)


@router.get("/directory", response_model=List[AccountPublic])
def account_directory(_: UserPublic = Depends(get_current_user)):
    """Every account's number and name (no balances): used to pick who to pay."""
    return service.list_accounts()


@router.get("/{account_id}", response_model=Account)
def get_account(account_id: int, user: UserPublic = Depends(get_current_user)):
    try:
        account = service.get_account(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if not is_admin(user) and account.customer_id != user.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can only view your own accounts")
    return account


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, _: UserPublic = Depends(require_admin)):
    try:
        return service.create_account(data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{account_id}", response_model=Account)
def update_account(account_id: int, data: AccountUpdate, _: UserPublic = Depends(require_admin)):
    try:
        return service.update_account(account_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{account_id}", response_model=Account)
def deactivate_account(account_id: int, _: UserPublic = Depends(require_admin)):
    try:
        return service.deactivate_account(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
