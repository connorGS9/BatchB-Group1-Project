# controllers/analytics_controller.py
# API layer for reports built with MongoDB aggregation pipelines.
from typing import List

from fastapi import APIRouter

from dependencies import analytics_service as service
from models.analytics import BranchBalanceSummary, BranchMonthlyVolume

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/branches/monthly-volume", response_model=List[BranchMonthlyVolume])
def branch_monthly_volume():
    """Money sent out of each branch, per month."""
    return service.branch_monthly_volume()


@router.get("/branches/balances", response_model=List[BranchBalanceSummary])
def branch_balances():
    """Active accounts, total and average balance per branch."""
    return service.branch_balances()
