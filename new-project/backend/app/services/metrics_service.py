"""Service to compute dashboard KPIs and basic metrics."""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

# Reuse consolidated models
from ..models import Alert, Case, TriageRun


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def _count_alerts_in_queue(self) -> int:
        """
        Count alerts considered "in queue" for triage.

        Heuristic: status in one of open states (case-insensitive):
        ["open", "queued", "new", "pending"]. If statuses are not standardized,
        this will still work case-insensitively; if none match, falls back to total alerts.
        """
        statuses = ["open", "queued", "new", "pending"]
        count = (
            self.db.query(func.count(Alert.id))
            .filter(func.lower(Alert.status).in_(statuses))
            .scalar()
        )
        if count is None:
            count = 0
        # Fallback: if no such statuses exist in data, return total alerts as queue size
        if count == 0:
            total = self.db.query(func.count(Alert.id)).scalar() or 0
            return int(total)
        return int(count)

    def _count_disputes_opened(self) -> int:
        """Count cases that are disputes and currently OPEN (case-insensitive)."""
        count = (
            self.db.query(func.count(Case.id))
            .filter(func.lower(Case.status) == "open")
            .filter(func.lower(Case.type).like("%dispute%"))
            .scalar()
        )
        if count is None:
            count = 0
        # If dataset doesn't mark type containing 'dispute', fall back to all OPEN cases
        if count == 0:
            fallback = (
                self.db.query(func.count(Case.id))
                .filter(func.lower(Case.status) == "open")
                .scalar()
            ) or 0
            return int(fallback)
        return int(count)

    def _avg_triage_latency_ms(self) -> Optional[int]:
        """
        Average triage latency in ms across all completed triage runs.
        Returns an integer ms or None when not available.
        """
        avg_val = self.db.query(func.avg(TriageRun.latency_ms)).scalar()
        if avg_val is None:
            return None
        try:
            return int(round(float(avg_val)))
        except Exception:
            return None

    def get_kpis(self) -> Dict[str, Optional[int]]:
        """Compute and return KPI values expected by the frontend."""
        return {
            "alertsInQueue": self._count_alerts_in_queue(),
            "disputesOpened": self._count_disputes_opened(),
            "avgTriageLatencyMs": self._avg_triage_latency_ms(),
        }
