"""
Compliance Agent: Enforces policy rules, OTP requirements, and identity verification.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..utils.logger import setup_logging, log_service_call

logger = setup_logging("compliance_agent")


class ComplianceAgent:
    """
    Enforces compliance policies including OTP verification, 
    identity gates, and policy restrictions.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.timeout = 5  # seconds
        
        # Compliance thresholds
        self.otp_threshold_amount = 500.0
        self.international_otp_required = True
        self.max_daily_transaction_count = 50
        self.max_daily_amount = 10000.0
    
    @log_service_call(logger)
    def check_compliance(
        self,
        customer_id: str,
        transaction: Dict[str, Any],
        profile: Dict[str, Any],
        proposed_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive compliance checks.
        
        Args:
            customer_id: Customer identifier
            transaction: Transaction to check
            profile: Customer profile
            proposed_action: Proposed action (e.g., freeze_card, unfreeze)
            
        Returns:
            Compliance check results with violations and requirements
        """
        start_time = time.time()
        
        try:
            violations = []
            requirements = []
            risk_flags = []
            compliance_score = 100  # Start at 100, deduct for violations
            
            # Check OTP requirements
            otp_check = self._check_otp_requirements(transaction, profile)
            if not otp_check["compliant"]:
                violations.append(otp_check)
                requirements.append("OTP verification required")
                compliance_score -= 30
            
            # Check identity verification
            identity_check = self._check_identity_verification(profile, transaction)
            if not identity_check["compliant"]:
                violations.append(identity_check)
                requirements.append("Identity verification required")
                compliance_score -= 25
            
            # Check transaction limits
            limit_check = self._check_transaction_limits(transaction, profile)
            if not limit_check["compliant"]:
                violations.append(limit_check)
                risk_flags.append("Transaction limit exceeded")
                compliance_score -= 20
            
            # Check account status
            status_check = self._check_account_status(profile)
            if not status_check["compliant"]:
                violations.append(status_check)
                risk_flags.append("Account status issue")
                compliance_score -= 35
            
            # Check action-specific policies
            if proposed_action:
                action_check = self._check_action_policy(proposed_action, profile, transaction)
                if not action_check["compliant"]:
                    violations.append(action_check)
                    requirements.extend(action_check.get("requirements", []))
                    compliance_score -= 15
            
            # Check regulatory requirements (PSD2, SCA, etc.)
            regulatory_check = self._check_regulatory_compliance(transaction, profile)
            if not regulatory_check["compliant"]:
                violations.append(regulatory_check)
                requirements.extend(regulatory_check.get("requirements", []))
                compliance_score -= 40
            
            # Determine overall compliance status
            is_compliant = len(violations) == 0
            status = "compliant" if is_compliant else "non_compliant"
            
            if len(violations) > 0 and all(v.get("severity") == "warning" for v in violations):
                status = "conditional"
            
            result = {
                "success": True,
                "customer_id": customer_id,
                "transaction_id": transaction.get("id"),
                "compliance_status": status,
                "is_compliant": is_compliant,
                "compliance_score": max(0, compliance_score),
                "violations": violations,
                "requirements": list(set(requirements)),
                "risk_flags": risk_flags,
                "can_proceed": is_compliant or status == "conditional",
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "duration": time.time() - start_time
            }
            
            logger.info(
                f"Compliance check for customer {customer_id}: "
                f"status={status}, violations={len(violations)}, score={compliance_score}"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in compliance check: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _check_otp_requirements(self, transaction: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Check if OTP verification is required."""
        amount = float(transaction.get("amount", 0))
        is_international = transaction.get("is_international", False)
        otp_verified = transaction.get("otp_verified", False)
        
        requires_otp = False
        reasons = []
        
        # High-value transactions
        if amount > self.otp_threshold_amount:
            requires_otp = True
            reasons.append(f"Transaction amount ${amount:.2f} exceeds OTP threshold (${self.otp_threshold_amount})")
        
        # International transactions
        if is_international and self.international_otp_required:
            requires_otp = True
            reasons.append("International transaction requires OTP verification")
        
        # First transaction on new device
        if transaction.get("is_new_device", False):
            requires_otp = True
            reasons.append("First transaction on new device requires OTP")
        
        compliant = not requires_otp or otp_verified
        
        return {
            "check": "otp_verification",
            "compliant": compliant,
            "requires_otp": requires_otp,
            "otp_verified": otp_verified,
            "reasons": reasons,
            "severity": "critical" if not compliant else "info",
            "requirements": ["OTP verification via SMS or authenticator app"] if not compliant else []
        }
    
    def _check_identity_verification(self, profile: Dict[str, Any], transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Check identity verification status."""
        identity_verified = profile.get("identity_verified", False)
        kyc_status = profile.get("kyc_status", "pending")
        account_age_days = profile.get("account_age_days", 0)
        
        reasons = []
        compliant = True
        
        # Identity not verified for high-risk transaction
        if not identity_verified and float(transaction.get("amount", 0)) > 1000:
            compliant = False
            reasons.append("Identity verification required for transactions >$1000")
        
        # KYC not complete
        if kyc_status != "approved":
            if float(transaction.get("amount", 0)) > 2000:
                compliant = False
                reasons.append(f"KYC approval required (current status: {kyc_status})")
        
        # New account without verification
        if account_age_days < 7 and not identity_verified:
            compliant = False
            reasons.append(f"New account ({account_age_days} days old) requires identity verification")
        
        return {
            "check": "identity_verification",
            "compliant": compliant,
            "identity_verified": identity_verified,
            "kyc_status": kyc_status,
            "reasons": reasons,
            "severity": "high" if not compliant else "info"
        }
    
    def _check_transaction_limits(self, transaction: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Check transaction limits and velocity."""
        amount = float(transaction.get("amount", 0))
        daily_tx_count = profile.get("daily_transaction_count", 0)
        daily_amount = profile.get("daily_transaction_amount", 0)
        
        reasons = []
        compliant = True
        
        # Daily count limit
        if daily_tx_count >= self.max_daily_transaction_count:
            compliant = False
            reasons.append(f"Daily transaction limit reached ({daily_tx_count}/{self.max_daily_transaction_count})")
        
        # Daily amount limit
        if daily_amount + amount > self.max_daily_amount:
            compliant = False
            reasons.append(
                f"Daily amount limit would be exceeded "
                f"(${daily_amount + amount:.2f}/${self.max_daily_amount})"
            )
        
        # Single transaction limit
        single_tx_limit = profile.get("single_transaction_limit", 5000)
        if amount > single_tx_limit:
            compliant = False
            reasons.append(f"Transaction amount ${amount:.2f} exceeds single transaction limit (${single_tx_limit})")
        
        return {
            "check": "transaction_limits",
            "compliant": compliant,
            "daily_count": daily_tx_count,
            "daily_amount": daily_amount,
            "reasons": reasons,
            "severity": "medium" if not compliant else "info"
        }
    
    def _check_account_status(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Check account status and restrictions."""
        account_status = profile.get("account_status", "active")
        card_status = profile.get("card_status", "active")
        is_frozen = profile.get("is_frozen", False)
        
        reasons = []
        compliant = True
        
        # Account inactive or suspended
        if account_status not in ["active", "verified"]:
            compliant = False
            reasons.append(f"Account status is '{account_status}' (must be 'active' or 'verified')")
        
        # Card frozen or blocked
        if is_frozen or card_status in ["frozen", "blocked", "closed"]:
            compliant = False
            reasons.append(f"Card is {card_status or 'frozen'}")
        
        return {
            "check": "account_status",
            "compliant": compliant,
            "account_status": account_status,
            "card_status": card_status,
            "is_frozen": is_frozen,
            "reasons": reasons,
            "severity": "critical" if not compliant else "info"
        }
    
    def _check_action_policy(
        self, 
        action: str, 
        profile: Dict[str, Any], 
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if proposed action complies with policies."""
        reasons = []
        requirements = []
        compliant = True
        
        # Unfreeze requires verification
        if action == "unfreeze_card":
            if not profile.get("identity_verified", False):
                compliant = False
                reasons.append("Cannot unfreeze card without identity verification")
                requirements.append("Identity verification required before unfreezing")
        
        # Dispute opening limits
        if action == "open_dispute":
            dispute_count = profile.get("dispute_count", 0)
            if dispute_count >= 5:
                compliant = False
                reasons.append(f"Customer has reached dispute limit ({dispute_count} disputes)")
                requirements.append("Manual review required for additional disputes")
        
        # Large refunds require approval
        if action == "issue_refund":
            amount = float(transaction.get("amount", 0))
            if amount > 1000:
                compliant = False
                reasons.append(f"Refunds over $1000 require manager approval")
                requirements.append("Manager approval required")
        
        return {
            "check": "action_policy",
            "compliant": compliant,
            "action": action,
            "reasons": reasons,
            "requirements": requirements,
            "severity": "warning" if not compliant else "info"
        }
    
    def _check_regulatory_compliance(self, transaction: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Check regulatory compliance (PSD2, SCA, etc.)."""
        reasons = []
        requirements = []
        compliant = True
        
        amount = float(transaction.get("amount", 0))
        is_international = transaction.get("is_international", False)
        sca_completed = transaction.get("sca_completed", False)
        
        # PSD2/SCA requirements (EU regulations)
        if is_international:
            # Strong Customer Authentication required for >€30
            if amount > 30 and not sca_completed:
                compliant = False
                reasons.append("PSD2/SCA required for international transactions >€30")
                requirements.append("Strong Customer Authentication (2FA) required")
        
        # AML/KYC requirements
        if amount > 3000:
            kyc_status = profile.get("kyc_status")
            if kyc_status != "approved":
                compliant = False
                reasons.append("AML/KYC verification required for transactions >$3000")
                requirements.append("Complete KYC verification")
        
        return {
            "check": "regulatory_compliance",
            "compliant": compliant,
            "reasons": reasons,
            "requirements": requirements,
            "severity": "high" if not compliant else "info"
        }
