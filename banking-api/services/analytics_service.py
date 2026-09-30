# services/analytics_service.py
# Business layer for reports. The heavy lifting happens in MongoDB
# (see repository/analytics_repository.py).
from typing import List

from models.analytics import BranchBalanceSummary, BranchMonthlyVolume
from repository.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository = None):
        self._repo = repository or AnalyticsRepository()

    def branch_monthly_volume(self) -> List[BranchMonthlyVolume]:
        return [BranchMonthlyVolume(**row) for row in self._repo.branch_monthly_volume()]

    def branch_balances(self) -> List[BranchBalanceSummary]:
        return [BranchBalanceSummary(**row) for row in self._repo.branch_balances()]
