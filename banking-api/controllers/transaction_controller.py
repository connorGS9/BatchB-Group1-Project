# controllers/transaction_controller.py
# API layer for transactions: transfer endpoint + filtered ledger listing.
# Access: admins -> every transaction, any transfer. Customers -> only transactions
# on their own accounts, and only transfers FROM their own account.
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import account_service, transaction_service as service
from errors import ForbiddenError, NotFoundError, ValidationError
from models.transaction import Transaction, TransactionType, TransferRequest
from models.user import UserPublic
from security import get_current_user, is_admin

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("/", response_model=List[Transaction])
def list_transactions(
    start_date: Optional[date] = Query(None, description="Only transactions on/after this date (YYYY-MM-DD)"),
    type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    user: UserPublic = Depends(get_current_user),
):
    account_ids = None
    if not is_admin(user):
        account_ids = [a.id for a in account_service.list_accounts(customer_id=user.customer_id)]
    return service.list_transactions(start_date=start_date, type=type, account_ids=account_ids)


@router.post("/transfer", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def transfer(data: TransferRequest, user: UserPublic = Depends(get_current_user)):
    acting_customer_id = None if is_admin(user) else user.customer_id
    try:
        return service.transfer(data, acting_customer_id=acting_customer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
