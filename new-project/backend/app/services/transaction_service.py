"""Service for handling transaction operations and alerts."""
from typing import List, Optional
from sqlalchemy.orm import Session
# Use package-relative imports to reference model modules within the app package
from ..models import Transaction, TransactionTrace, Alert

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_transaction(self, txn_id: str) -> Optional[Transaction]:
        """Get a transaction by ID."""
        return self.db.query(Transaction)\
                     .filter(Transaction.id == txn_id)\
                     .first()
    
    def list_transactions(self, customer_id: Optional[str] = None) -> List[Transaction]:
        """List transactions, optionally filtered by customer."""
        query = self.db.query(Transaction)
        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        return query.all()
    
    def get_transaction_trace(self, txn_id: str) -> Optional[TransactionTrace]:
        """Get trace data for a transaction."""
        return self.db.query(TransactionTrace)\
                     .filter(TransactionTrace.txn_id == txn_id)\
                     .first()
    
    def create_alert(self, customer_id: str, txn_id: str, risk: str) -> Alert:
        """Create a new alert for a suspicious transaction."""
        alert = Alert(
            customer_id=customer_id,
            suspect_txn_id=txn_id,
            risk=risk,
            status="NEW"
        )
        self.db.add(alert)
        self.db.commit()
        return alert
    
    def get_alerts(self, 
                   customer_id: Optional[str] = None,
                   status: Optional[str] = None) -> List[Alert]:
        """Get alerts, optionally filtered by customer and status."""
        query = self.db.query(Alert)
        if customer_id:
            query = query.filter(Alert.customer_id == customer_id)
        if status:
            query = query.filter(Alert.status == status)
        return query.all()
    
    def update_alert_status(self, alert_id: str, new_status: str) -> Alert:
        """Update an alert's status."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
            
        alert.status = new_status
        self.db.commit()
        return alert