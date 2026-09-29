# controllers/account_controller.py
# API layer: maps HTTP requests to the service and domain errors to status codes.
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from dependencies import account_service as service
from errors import NotFoundError, ValidationError
from models.account import Account, AccountCreate, AccountUpdate

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("/", response_model=List[Account])
def list_accounts(
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    min_balance: Optional[float] = Query(None, description="Only accounts with balance >= this"),
    customer_id: Optional[int] = Query(None, description="Only accounts owned by this customer"),
):
    return service.list_accounts(branch_id=branch_id, min_balance=min_balance,
                                 customer_id=customer_id)


@router.get("/{account_id}", response_model=Account)
def get_account(account_id: int):
    try:
        return service.get_account(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate):
    try:
        return service.create_account(data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{account_id}", response_model=Account)
def update_account(account_id: int, data: AccountUpdate):
    try:
        return service.update_account(account_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{account_id}", response_model=Account)
def deactivate_account(account_id: int):
    try:
        return service.deactivate_account(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
