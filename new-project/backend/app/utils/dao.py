from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
# Import specific model classes from the models package modules
from ..models import Customer, Transaction
from ..models.models import KbDoc
from sqlalchemy import select, desc, and_

def get_customer(db: Session, customer_id: str) -> Optional[Customer]:
    return db.get(Customer, customer_id)

def create_customer(db: Session, customer: Customer) -> Customer:
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def get_transactions_by_customer(db: Session, customer_id: str, limit: int = 50, cursor_ts: Optional[str] = None) -> Tuple[List[Transaction], Optional[str]]:
    """Keyset pagination by timestamp (ts DESC). Cursor is ISO timestamp string."""
    stmt = select(Transaction).where(Transaction.customer_id == customer_id)
    if cursor_ts:
        stmt = stmt.where(Transaction.ts < cursor_ts)
    stmt = stmt.order_by(desc(Transaction.ts)).limit(limit)
    rows = db.execute(stmt).scalars().all()
    next_cursor = None
    if rows:
        last = rows[-1]
        next_cursor = last.ts.isoformat()
    return rows, next_cursor

def search_kb(db: Session, q: str, limit: int = 20) -> List[KbDoc]:
    if not q:
        return []
    stmt = select(KbDoc).where(KbDoc.content_text.ilike(f"%{q}%") | KbDoc.title.ilike(f"%{q}%")).limit(limit)
    return db.execute(stmt).scalars().all()
