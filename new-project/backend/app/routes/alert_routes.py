from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.models import Alert
from fastapi import Depends
from typing import List, Optional

router = APIRouter()

@router.get("/alerts")
def get_alerts(
    status: Optional[str] = None,
    risk: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get list of alerts with optional filtering"""
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status.upper())
    
    if risk:
        query = query.filter(Alert.risk == risk.upper())
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": str(alert.id),
            "status": alert.status,
            "risk": alert.risk,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "suspect_txn_id": str(alert.suspect_txn_id) if alert.suspect_txn_id else None,
            "customer_id": str(alert.customer_id)
        }
        for alert in alerts
    ]

@router.get("/alerts/{alert_id}")
def get_alert(alert_id: str, db: Session = Depends(get_db)) -> dict:
    """Get details of a specific alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "id": str(alert.id),
        "status": alert.status,
        "risk": alert.risk,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "suspect_txn_id": str(alert.suspect_txn_id) if alert.suspect_txn_id else None,
        "customer_id": str(alert.customer_id)
    }
