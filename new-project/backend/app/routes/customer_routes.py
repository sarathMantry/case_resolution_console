"""API routes for customer operations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..services.customer_service import CustomerService
from ..utils.database import get_db
from ..models import Customer, Case, Transaction

router = APIRouter(prefix="/customers")

@router.get("/{customer_id}", response_model=None)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer_service = CustomerService(db)
    customer = customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.get("/", response_model=None)
def list_customers(db: Session = Depends(get_db)):
    customer_service = CustomerService(db)
    return customer_service.list_customers()

@router.get("/{customer_id}/cases", response_model=None)
def get_customer_cases(customer_id: str, db: Session = Depends(get_db)):
    customer_service = CustomerService(db)
    if not customer_service.get_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_service.get_customer_cases(customer_id)

@router.get("/{customer_id}/transactions", response_model=None)
def get_customer_transactions(customer_id: str, db: Session = Depends(get_db)):
    customer_service = CustomerService(db)
    if not customer_service.get_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_service.get_customer_transactions(customer_id)

@router.put("/{customer_id}/risk-level", response_model=None)
def update_customer_risk_level(
    customer_id: str,
    risk_level: str,
    db: Session = Depends(get_db)
):
    customer_service = CustomerService(db)
    try:
        return customer_service.update_customer_risk_level(
            customer_id=customer_id,
            risk_level=risk_level
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))