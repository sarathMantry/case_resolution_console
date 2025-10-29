"""Service for handling customer data and operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
# Use package-relative imports to reference model modules within the app package
from ..models import Customer, Case, Transaction

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID."""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def list_customers(self) -> List[Customer]:
        """List all customers."""
        return self.db.query(Customer).all()
    
    def get_customer_cases(self, customer_id: str) -> List[Case]:
        """Get all cases for a customer."""
        return self.db.query(Case)\
                     .filter(Case.customer_id == customer_id)\
                     .all()
    
    def get_customer_transactions(self, customer_id: str) -> List[Transaction]:
        """Get all transactions for a customer."""
        return self.db.query(Transaction)\
                     .filter(Transaction.customer_id == customer_id)\
                     .all()
    
    def update_customer_risk_level(self, customer_id: str, risk_level: str) -> Customer:
        """Update a customer's risk level."""
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
            
        customer.risk_level = risk_level
        self.db.commit()
        
        return customer