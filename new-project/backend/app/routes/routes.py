from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .db import get_db
from .services import CustomerService
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class TransactionsResponse(BaseModel):
    items: list
    nextCursor: Optional[str]

@router.get('/api/customer/{customer_id}/transactions', response_model=TransactionsResponse)
def customer_transactions(customer_id: str, limit: int = Query(50, ge=1, le=100), cursor: Optional[str] = None, db: Session = Depends(get_db)):
    svc = CustomerService(db)
    customer = svc.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail='customer not found')
    rows, next_cursor = svc.get_transactions(customer_id, limit=limit, cursor=cursor)
    # Serialize minimal transaction fields
    items = [
        {
            'id': r.id,
            'card_id': r.card_id,
            'merchant': r.merchant,
            'amount_cents': r.amount_cents,
            'currency': r.currency,
            'ts': r.ts.isoformat()
        }
        for r in rows
    ]
    return {'items': items, 'nextCursor': next_cursor}

@router.get('/api/kb/search')
def kb_search(q: Optional[str] = Query('', min_length=0), db: Session = Depends(get_db)):
    svc = CustomerService(db)
    results = svc.search_kb(q)
    return {'results': [{'docId': r.id, 'title': r.title, 'anchor': r.anchor, 'extract': (r.content_text[:200] + '...') if len(r.content_text) > 200 else r.content_text} for r in results]}
