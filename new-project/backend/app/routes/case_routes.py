"""API routes for case management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..services.case_service import CaseService
from ..utils.database import get_db
from ..models import Case, CaseEvent

router = APIRouter(prefix="/cases")

@router.get("/{case_id}", response_model=None)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case_service = CaseService(db)
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.get("/", response_model=None)
def list_cases(customer_id: str = None, db: Session = Depends(get_db)):
    case_service = CaseService(db)
    return case_service.list_cases(customer_id)

@router.post("/", response_model=None)
def create_case(
    customer_id: str,
    txn_id: str,
    case_type: str,
    reason_code: str,
    actor: str,
    db: Session = Depends(get_db)
):
    case_service = CaseService(db)
    return case_service.create_case(
        customer_id=customer_id,
        txn_id=txn_id,
        case_type=case_type,
        reason_code=reason_code,
        actor=actor
    )

@router.put("/{case_id}/status", response_model=None)
def update_case_status(
    case_id: str,
    new_status: str,
    actor: str,
    notes: str = None,
    db: Session = Depends(get_db)
):
    case_service = CaseService(db)
    try:
        return case_service.update_case_status(
            case_id=case_id,
            new_status=new_status,
            actor=actor,
            notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{case_id}/events", response_model=None)
def get_case_events(case_id: str, db: Session = Depends(get_db)):
    case_service = CaseService(db)
    return case_service.get_case_events(case_id)