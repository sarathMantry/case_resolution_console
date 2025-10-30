"""Service for handling triage operations."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
from datetime import datetime

from ..models import Alert, TriageRun, AgentTrace, Transaction, Customer, Case
from ..utils.logger import setup_logging, log_service_call, safe_log_data
from ..utils.metrics import record_triage_operation, record_triage_action
import time

# Set up logger for triage service
logger = setup_logging(__name__)


class TriageService:
    def __init__(self, db: Session):
        self.db = db
        logger.debug("TriageService initialized")
    
    @log_service_call(logger)
    def get_triage_details(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive triage details for an alert."""
        logger.info(f"Fetching triage details for alert: {alert_id}")
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return None
        
        # Get customer
        customer = self.db.query(Customer).filter(Customer.id == alert.customer_id).first()
        
        # Get transaction
        transaction = self.db.query(Transaction).filter(
            Transaction.id == alert.suspect_txn_id
        ).first() if alert.suspect_txn_id else None
        
        # Get latest triage run
        triage_run = self.db.query(TriageRun)\
            .filter(TriageRun.alert_id == alert_id)\
            .order_by(desc(TriageRun.started_at))\
            .first()
        
        # Get agent traces if triage run exists
        tool_calls = []
        if triage_run:
            traces = self.db.query(AgentTrace)\
                .filter(AgentTrace.run_id == triage_run.id)\
                .order_by(AgentTrace.seq)\
                .all()
            
            tool_calls = [
                {
                    "step": trace.step,
                    "ok": trace.ok,
                    "duration_ms": trace.duration_ms,
                    "detail": trace.detail_json,
                    "seq": trace.seq
                }
                for trace in traces
            ]
        
        # Build response
        return {
            "alert_id": alert.id,
            "customer_id": alert.customer_id,
            "status": alert.status,
            "created_at": alert.created_at.isoformat(),
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email_masked": customer.email_masked,
                "kyc_level": customer.kyc_level
            } if customer else None,
            "transaction": {
                "id": transaction.id,
                "merchant": transaction.merchant,
                "amount_cents": transaction.amount_cents,
                "currency": transaction.currency,
                "ts": transaction.ts.isoformat(),
                "mcc": transaction.mcc,
                "city": transaction.city,
                "country": transaction.country
            } if transaction else None,
            "triage": {
                "risk": triage_run.risk if triage_run else alert.risk,
                "reasons": triage_run.reasons if triage_run else {"reasons": []},
                "fallback_used": triage_run.fallback_used if triage_run else False,
                "latency_ms": triage_run.latency_ms if triage_run else None,
                "started_at": triage_run.started_at.isoformat() if triage_run else None,
                "ended_at": triage_run.ended_at.isoformat() if triage_run else None
            },
            "tool_calls": tool_calls,
            "recommended_action": self._get_recommended_action(alert, triage_run),
            "citations": self._get_citations(triage_run) if triage_run else []
        }
    
    def _get_recommended_action(self, alert: Alert, triage_run: Optional[TriageRun]) -> str:
        """Determine recommended action based on risk level."""
        risk = triage_run.risk if triage_run else alert.risk
        risk_level = risk.upper()
        
        if risk_level == "HIGH":
            return "FREEZE_CARD"
        elif risk_level == "MEDIUM":
            return "CONTACT_CUSTOMER"
        elif risk_level == "LOW":
            return "MONITOR"
        else:
            return "REVIEW_MANUALLY"
    
    def _get_citations(self, triage_run: TriageRun) -> List[Dict[str, str]]:
        """Extract citations from triage run reasons."""
        citations = []
        reasons = triage_run.reasons
        
        # Mock citations based on reasons
        if isinstance(reasons, dict) and "reasons" in reasons:
            for idx, reason in enumerate(reasons["reasons"][:3]):
                citations.append({
                    "title": f"Policy Reference {idx + 1}",
                    "text": f"Related to: {reason}",
                    "source": "internal_policy"
                })
        
        return citations
    
    @log_service_call(logger)
    def freeze_card(self, alert_id: str) -> Dict[str, Any]:
        """Freeze the card associated with an alert (idempotent)."""
        start_time = time.time()
        logger.info(f"Attempting to freeze card for alert: {alert_id}")
        
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                logger.error(f"Alert not found for freeze_card: {alert_id}")
                record_triage_action("freeze_card", "error", False)
                raise ValueError(f"Alert {alert_id} not found")
            
            # Check if already in review (idempotency)
            if alert.status == "IN_REVIEW":
                logger.info(f"Card already frozen for alert: {alert_id} (idempotent)")
                duration = time.time() - start_time
                record_triage_action("freeze_card", "success", already_processed=True)
                record_triage_operation("freeze_card", "idempotent", duration)
                return {
                    "success": True,
                    "action": "freeze_card",
                    "alert_id": alert_id,
                    "already_processed": True,
                    "message": "Card already frozen (alert already in review)"
                }
            
            # Update alert status
            alert.status = "IN_REVIEW"
            self.db.commit()
            logger.info(f"Card frozen successfully for alert: {alert_id}")
            
            duration = time.time() - start_time
            record_triage_action("freeze_card", "success", already_processed=False)
            record_triage_operation("freeze_card", "success", duration)
            
            return {
                "success": True,
                "action": "freeze_card",
                "alert_id": alert_id,
                "already_processed": False
            }
        except Exception as e:
            duration = time.time() - start_time
            record_triage_operation("freeze_card", "error", duration)
            raise
    
    @log_service_call(logger)
    def open_dispute(self, alert_id: str, reason_code: str = "unauthorized") -> Dict[str, Any]:
        """Open a dispute case for an alert (idempotent)."""
        start_time = time.time()
        logger.info(f"Opening dispute for alert: {alert_id}, reason: {reason_code}")
        
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                logger.error(f"Alert not found for open_dispute: {alert_id}")
                record_triage_action("open_dispute", "error", False)
                raise ValueError(f"Alert {alert_id} not found")
            
            # Check if dispute already exists for this alert (idempotency)
            existing_case = self.db.query(Case).filter(
                Case.customer_id == alert.customer_id,
                Case.txn_id == alert.suspect_txn_id,
                Case.type == "dispute"
            ).first()
            
            if existing_case:
                logger.info(f"Dispute already exists for alert: {alert_id}, case_id: {existing_case.id} (idempotent)")
                duration = time.time() - start_time
                record_triage_action("open_dispute", "success", already_processed=True)
                record_triage_operation("open_dispute", "idempotent", duration)
                return {
                    "success": True,
                    "action": "open_dispute",
                    "case_id": existing_case.id,
                    "alert_id": alert_id,
                    "already_processed": True,
                    "message": f"Dispute already exists (case_id: {existing_case.id})"
                }
            
            # Create case
            case = Case(
                id=str(uuid.uuid4()),
                customer_id=alert.customer_id,
                txn_id=alert.suspect_txn_id,
                type="dispute",
                status="open",
                reason_code=reason_code,
                created_at=datetime.utcnow()
            )
            self.db.add(case)
            
            # Update alert status
            alert.status = "IN_REVIEW"
            self.db.commit()
            logger.info(f"Dispute created successfully for alert: {alert_id}, case_id: {case.id}")
            
            duration = time.time() - start_time
            record_triage_action("open_dispute", "success", already_processed=False)
            record_triage_operation("open_dispute", "success", duration)
            
            return {
                "success": True,
                "action": "open_dispute",
                "case_id": case.id,
                "alert_id": alert_id,
                "already_processed": False
            }
        except Exception as e:
            duration = time.time() - start_time
            record_triage_operation("open_dispute", "error", duration)
            raise
    
    @log_service_call(logger)
    def contact_customer(self, alert_id: str) -> Dict[str, Any]:
        """Mark alert for customer contact."""
        logger.info(f"Marking alert for customer contact: {alert_id}")
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        
        alert.status = "IN_REVIEW"
        self.db.commit()
        logger.info(f"Alert marked for customer contact: {alert_id}")
        
        return {"success": True, "action": "contact_customer", "alert_id": alert_id}
    
    @log_service_call(logger)
    def mark_false_positive(self, alert_id: str) -> Dict[str, Any]:
        """Mark an alert as a false positive (idempotent)."""
        logger.info(f"Marking alert as false positive: {alert_id}")
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert not found for mark_false_positive: {alert_id}")
            raise ValueError(f"Alert {alert_id} not found")
        
        # Check if already closed (idempotency)
        if alert.status == "CLOSED":
            logger.info(f"Alert already marked as false positive: {alert_id} (idempotent)")
            return {
                "success": True,
                "action": "mark_false_positive",
                "alert_id": alert_id,
                "already_processed": True,
                "message": "Alert already marked as false positive (status is CLOSED)"
            }
        
        alert.status = "CLOSED"
        self.db.commit()
        logger.info(f"Alert marked as false positive: {alert_id}")
        
        return {
            "success": True,
            "action": "mark_false_positive",
            "alert_id": alert_id,
            "already_processed": False
        }
