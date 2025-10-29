"""Service for handling case management functionality."""
from typing import List, Optional
from sqlalchemy.orm import Session
# Use package-relative imports to reference model modules within the app package
from ..models import Case, CaseEvent, Customer, Transaction

class CaseService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_case(self, case_id: str) -> Optional[Case]:
        """Get a case by ID."""
        return self.db.query(Case).filter(Case.id == case_id).first()
    
    def list_cases(self, customer_id: Optional[str] = None) -> List[Case]:
        """List all cases, optionally filtered by customer."""
        query = self.db.query(Case)
        if customer_id:
            query = query.filter(Case.customer_id == customer_id)
        return query.all()
    
    def create_case(self, 
                    customer_id: str,
                    txn_id: str,
                    case_type: str,
                    reason_code: str,
                    actor: str) -> Case:
        """Create a new case and initial case event."""
        case = Case(
            customer_id=customer_id,
            txn_id=txn_id,
            type=case_type,
            status="OPEN",
            reason_code=reason_code
        )
        self.db.add(case)
        
        # Create initial case event
        event = CaseEvent(
            case_id=case.id,
            actor=actor,
            action="CREATE",
            payload_json={"reason_code": reason_code}
        )
        self.db.add(event)
        self.db.commit()
        
        return case
    
    def update_case_status(self,
                          case_id: str,
                          new_status: str,
                          actor: str,
                          notes: Optional[str] = None) -> Case:
        """Update a case's status and create status change event."""
        case = self.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
            
        case.status = new_status
        
        event = CaseEvent(
            case_id=case.id,
            actor=actor,
            action="STATUS_CHANGE",
            payload_json={
                "old_status": case.status,
                "new_status": new_status,
                "notes": notes
            }
        )
        self.db.add(event)
        self.db.commit()
        
        return case
        
    def get_case_events(self, case_id: str) -> List[CaseEvent]:
        """Get all events for a case."""
        return self.db.query(CaseEvent)\
                     .filter(CaseEvent.case_id == case_id)\
                     .order_by(CaseEvent.ts.desc())\
                     .all()