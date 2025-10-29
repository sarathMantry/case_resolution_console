"""API routes for transaction and alert management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..services.transaction_service import TransactionService
from ..utils.database import get_db
from ..models import Transaction, TransactionTrace, Alert

router = APIRouter(prefix="/transactions")

@router.get("/{txn_id}", response_model=None)
def get_transaction(txn_id: str, db: Session = Depends(get_db)):
    transaction_service = TransactionService(db)
    transaction = transaction_service.get_transaction(txn_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.get("/", response_model=None)
def list_transactions(customer_id: Optional[str] = None, db: Session = Depends(get_db)):
    transaction_service = TransactionService(db)
    return transaction_service.list_transactions(customer_id)

@router.get("/{txn_id}/trace", response_model=None)
def get_transaction_trace(txn_id: str, db: Session = Depends(get_db)):
    transaction_service = TransactionService(db)
    trace = transaction_service.get_transaction_trace(txn_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Transaction trace not found")
    return trace

# Alert routes
@router.post("/alerts", response_model=None)
def create_alert(
    customer_id: str,
    txn_id: str,
    risk: str,
    db: Session = Depends(get_db)
):
    transaction_service = TransactionService(db)
    return transaction_service.create_alert(
        customer_id=customer_id,
        txn_id=txn_id,
        risk=risk
    )

@router.get("/alerts", response_model=None)
def get_alerts(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    transaction_service = TransactionService(db)
    return transaction_service.get_alerts(
        customer_id=customer_id,
        status=status
    )

@router.put("/alerts/{alert_id}/status", response_model=None)
def update_alert_status(
    alert_id: str,
    new_status: str,
    db: Session = Depends(get_db)
):
    transaction_service = TransactionService(db)
    try:
        return transaction_service.update_alert_status(
            alert_id=alert_id,
            new_status=new_status
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))