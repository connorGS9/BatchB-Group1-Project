# controllers/customer_controller.py
# API layer: maps HTTP requests to the service and domain errors to status codes.
from typing import List

from fastapi import APIRouter, HTTPException, status

from dependencies import customer_service as service
from errors import NotFoundError, ValidationError
from models.customer import Customer, CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("/", response_model=List[Customer])
def list_customers():
    return service.list_customers()


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    try:
        return service.get_customer(customer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate):
    try:
        return service.create_customer(data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, data: CustomerUpdate):
    try:
        return service.update_customer(customer_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{customer_id}", response_model=Customer)
def deactivate_customer(customer_id: int):
    try:
        return service.deactivate_customer(customer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
