# controllers/customer_controller.py
# API layer: maps HTTP requests to the service and domain errors to status codes.
# Access: admins -> everything. Customers -> read/update only their OWN record.
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import customer_service as service
from errors import NotFoundError, ValidationError
from models.customer import Customer, CustomerCreate, CustomerUpdate
from models.user import UserPublic
from security import ensure_own_customer, get_current_user, require_admin

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("/", response_model=List[Customer])
def list_customers(_: UserPublic = Depends(require_admin)):
    return service.list_customers()


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, user: UserPublic = Depends(get_current_user)):
    ensure_own_customer(user, customer_id)
    try:
        return service.get_customer(customer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, _: UserPublic = Depends(require_admin)):
    try:
        return service.create_customer(data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, data: CustomerUpdate,
                    user: UserPublic = Depends(get_current_user)):
    ensure_own_customer(user, customer_id)   # the Settings page edits your own profile
    try:
        return service.update_customer(customer_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{customer_id}", response_model=Customer)
def deactivate_customer(customer_id: int, _: UserPublic = Depends(require_admin)):
    try:
        return service.deactivate_customer(customer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
