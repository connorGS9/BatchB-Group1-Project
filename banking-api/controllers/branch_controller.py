# controllers/branch_controller.py
# API layer: maps HTTP requests to the service and domain errors to status codes.
from typing import List

from fastapi import APIRouter, HTTPException, status

from dependencies import branch_service as service
from errors import NotFoundError
from models.branch import Branch, BranchCreate, BranchUpdate

router = APIRouter(prefix="/api/v1/branches", tags=["branches"])


@router.get("/", response_model=List[Branch])
def list_branches():
    return service.list_branches()


@router.get("/{branch_id}", response_model=Branch)
def get_branch(branch_id: int):
    try:
        return service.get_branch(branch_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=Branch, status_code=status.HTTP_201_CREATED)
def create_branch(data: BranchCreate):
    return service.create_branch(data)


@router.put("/{branch_id}", response_model=Branch)
def update_branch(branch_id: int, data: BranchUpdate):
    try:
        return service.update_branch(branch_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{branch_id}", response_model=Branch)
def deactivate_branch(branch_id: int):
    try:
        return service.deactivate_branch(branch_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
