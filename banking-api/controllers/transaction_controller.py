# controllers/transaction_controller.py
# API layer for transactions: transfer endpoint + filtered ledger listing.
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from dependencies import transaction_service as service
from errors import NotFoundError, ValidationError
from models.transaction import Transaction, TransactionType, TransferRequest

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("/", response_model=List[Transaction])
def list_transactions(
    start_date: Optional[date] = Query(None, description="Only transactions on/after this date (YYYY-MM-DD)"),
    type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
):
    return service.list_transactions(start_date=start_date, type=type)


@router.post("/transfer", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def transfer(data: TransferRequest):
    try:
        return service.transfer(data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
