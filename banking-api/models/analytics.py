from typing import Optional

from pydantic import BaseModel


class BranchMonthlyVolume(BaseModel):
    """Total money sent out of a branch's accounts in one month."""
    branch_id: int
    branch_name: Optional[str] = None
    year: int
    month: int
    total_amount: float
    transaction_count: int


class BranchBalanceSummary(BaseModel):
    """How much money a branch holds across its active accounts."""
    branch_id: int
    branch_name: Optional[str] = None
    account_count: int
    total_balance: float
    average_balance: float
