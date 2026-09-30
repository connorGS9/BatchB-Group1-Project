# controllers/analytics_controller.py
# API layer for reports built with MongoDB aggregation pipelines.
# Access: an admin token, OR another program sending the  X-API-Key: <key>  header.
from typing import List

from fastapi import APIRouter, Depends

from dependencies import analytics_service as service
from models.analytics import BranchBalanceSummary, BranchMonthlyVolume
from security import require_admin_or_api_key

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"],
                   dependencies=[Depends(require_admin_or_api_key)])


@router.get("/branches/monthly-volume", response_model=List[BranchMonthlyVolume])
def branch_monthly_volume():
    """Money sent out of each branch, per month."""
    return service.branch_monthly_volume()


@router.get("/branches/balances", response_model=List[BranchBalanceSummary])
def branch_balances():
    """Active accounts, total and average balance per branch."""
    return service.branch_balances()
