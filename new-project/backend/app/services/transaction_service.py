"""Service for handling transaction operations and alerts."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
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
        return query.order_by(Transaction.ts.desc()).all()
    
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            customer_id=transaction_data['customer_id'],
            card_id=transaction_data['card_id'],
            mcc=transaction_data['mcc'],
            merchant=transaction_data['merchant'],
            amount_cents=transaction_data['amount_cents'],
            currency=transaction_data.get('currency', 'USD'),
            ts=transaction_data.get('ts', datetime.utcnow()),
            device_id=transaction_data.get('device_id'),
            country=transaction_data.get('country', 'US'),
            city=transaction_data.get('city')
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def update_transaction(self, txn_id: str, transaction_data: Dict[str, Any]) -> Transaction:
        """Update an existing transaction."""
        transaction = self.get_transaction(txn_id)
        if not transaction:
            raise ValueError(f"Transaction {txn_id} not found")
        
        # Update allowed fields
        allowed_fields = ['mcc', 'merchant', 'amount_cents', 'currency', 'device_id', 'country', 'city']
        for field in allowed_fields:
            if field in transaction_data:
                setattr(transaction, field, transaction_data[field])
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def delete_transaction(self, txn_id: str) -> bool:
        """Delete a transaction."""
        transaction = self.get_transaction(txn_id)
        if not transaction:
            raise ValueError(f"Transaction {txn_id} not found")
        
        self.db.delete(transaction)
        self.db.commit()
        return True
    
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