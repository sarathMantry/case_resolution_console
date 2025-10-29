"""API routes for dashboard KPIs and metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..services.metrics_service import MetricsService
from ..utils.database import get_db


class KpisResponse(BaseModel):
    alertsInQueue: int
    disputesOpened: int
    avgTriageLatencyMs: int | None


router = APIRouter(prefix="/api/dashboard")


@router.get("/kpis", response_model=KpisResponse)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    svc = MetricsService(db)
    data = svc.get_kpis()
    return data
