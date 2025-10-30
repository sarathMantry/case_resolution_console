"""
Fraud Agent: Detects fraud signals including velocity, device changes, and risk scoring.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from ..utils.logger import setup_logging, log_service_call
from ..utils.gemini_llm import get_gemini_llm

logger = setup_logging("fraud_agent")


class FraudAgent:
    """
    Analyzes transactions for fraud signals using deterministic rules.
    Calculates risk score, identifies velocity issues, device changes, and MCC rarity.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.timeout = 15  # seconds
        self.llm = get_gemini_llm()
        
        # Risk score weights
        self.weights = {
            "velocity": 0.25,
            "device_change": 0.20,
            "mcc_rarity": 0.15,
            "chargebacks": 0.25,
            "amount_anomaly": 0.10,
            "location_change": 0.05
        }
    
    @log_service_call(logger)
    def analyze(
        self, 
        customer_id: str, 
        transaction_id: Optional[str],
        recent_transactions: List[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fraud analysis.
        
        Args:
            customer_id: Customer identifier
            transaction_id: Specific transaction to analyze (optional)
            recent_transactions: List of recent transactions
            profile: Customer profile data
            
        Returns:
            Fraud analysis with risk score, reasons, and recommended action
        """
        start_time = time.time()
        
        try:
            if not recent_transactions:
                return {
                    "success": False,
                    "error": "No transactions to analyze",
                    "duration": time.time() - start_time
                }
            
            # Find target transaction
            target_tx = None
            if transaction_id:
                target_tx = next((tx for tx in recent_transactions if tx.get("id") == transaction_id), None)
            else:
                target_tx = recent_transactions[0]  # Most recent
            
            if not target_tx:
                return {
                    "success": False,
                    "error": "Target transaction not found",
                    "duration": time.time() - start_time
                }
            
            # Perform fraud checks
            velocity_score, velocity_reasons = self._check_velocity(recent_transactions, target_tx)
            device_score, device_reasons = self._check_device_change(recent_transactions, target_tx)
            mcc_score, mcc_reasons = self._check_mcc_rarity(recent_transactions, target_tx)
            chargeback_score, chargeback_reasons = self._check_chargebacks(profile, recent_transactions)
            amount_score, amount_reasons = self._check_amount_anomaly(recent_transactions, target_tx)
            location_score, location_reasons = self._check_location_change(recent_transactions, target_tx)
            
            # Calculate weighted risk score
            risk_score = (
                velocity_score * self.weights["velocity"] +
                device_score * self.weights["device_change"] +
                mcc_score * self.weights["mcc_rarity"] +
                chargeback_score * self.weights["chargebacks"] +
                amount_score * self.weights["amount_anomaly"] +
                location_score * self.weights["location_change"]
            )
            
            # Collect all reasons
            all_reasons = (
                velocity_reasons + device_reasons + mcc_reasons + 
                chargeback_reasons + amount_reasons + location_reasons
            )
            
            # Determine action based on risk score
            action, risk_level = self._determine_action(risk_score, all_reasons)
            
            # Generate natural language reasoning using Gemini
            llm_reasoning = None
            if self.llm.enabled:
                try:
                    llm_reasoning = self.llm.generate_fraud_reasoning(
                        fraud_signals={
                            "signal_scores": {
                                "velocity": velocity_score,
                                "device_change": device_score,
                                "mcc_rarity": mcc_score,
                                "chargebacks": chargeback_score,
                                "amount_anomaly": amount_score,
                                "location_change": location_score
                            },
                            "reasons": all_reasons
                        },
                        transaction_data=target_tx,
                        customer_profile=profile
                    )
                except Exception as e:
                    logger.warning(f"LLM reasoning generation failed: {e}")
            
            result = {
                "success": True,
                "customer_id": customer_id,
                "transaction_id": target_tx.get("id"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "reasons": all_reasons,
                "llm_reasoning": llm_reasoning,
                "recommended_action": action,
                "signal_scores": {
                    "velocity": round(velocity_score, 2),
                    "device_change": round(device_score, 2),
                    "mcc_rarity": round(mcc_score, 2),
                    "chargebacks": round(chargeback_score, 2),
                    "amount_anomaly": round(amount_score, 2),
                    "location_change": round(location_score, 2)
                },
                "duration": time.time() - start_time
            }
            
            logger.info(
                f"Fraud analysis complete for customer {customer_id}: "
                f"risk_score={risk_score:.2f}, action={action}, reasons={len(all_reasons)}"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in fraud analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _check_velocity(self, transactions: List[Dict[str, Any]], target_tx: Dict[str, Any]) -> tuple[float, List[str]]:
        """Check transaction velocity (frequency over time)."""
        reasons = []
        score = 0.0
        
        try:
            target_time = datetime.fromisoformat(target_tx.get("timestamp", "").replace('Z', '+00:00'))
            
            # Count transactions in last hour
            hour_ago = target_time - timedelta(hours=1)
            tx_last_hour = sum(
                1 for tx in transactions 
                if datetime.fromisoformat(tx.get("timestamp", "").replace('Z', '+00:00')) > hour_ago
            )
            
            # Count transactions in last 24 hours
            day_ago = target_time - timedelta(days=1)
            tx_last_day = sum(
                1 for tx in transactions 
                if datetime.fromisoformat(tx.get("timestamp", "").replace('Z', '+00:00')) > day_ago
            )
            
            # High velocity in last hour
            if tx_last_hour > 5:
                score += 80
                reasons.append(f"High velocity: {tx_last_hour} transactions in last hour")
            elif tx_last_hour > 3:
                score += 50
                reasons.append(f"Elevated velocity: {tx_last_hour} transactions in last hour")
            
            # High daily velocity
            if tx_last_day > 20:
                score += 60
                reasons.append(f"High daily velocity: {tx_last_day} transactions in 24 hours")
            elif tx_last_day > 10:
                score += 30
                reasons.append(f"Elevated daily velocity: {tx_last_day} transactions in 24 hours")
            
        except Exception as e:
            logger.warning(f"Velocity check error: {e}")
        
        return min(score, 100), reasons
    
    def _check_device_change(self, transactions: List[Dict[str, Any]], target_tx: Dict[str, Any]) -> tuple[float, List[str]]:
        """Check for device fingerprint changes."""
        reasons = []
        score = 0.0
        
        try:
            devices = [tx.get("device_id") for tx in transactions if tx.get("device_id")]
            
            if len(set(devices)) > 3:
                score = 70
                reasons.append(f"Multiple devices detected: {len(set(devices))} unique devices")
            
            # Check for recent device change
            if len(transactions) >= 2:
                recent_devices = [tx.get("device_id") for tx in transactions[:5] if tx.get("device_id")]
                if recent_devices and len(set(recent_devices)) > 1:
                    score = max(score, 60)
                    reasons.append("Recent device change detected")
            
        except Exception as e:
            logger.warning(f"Device check error: {e}")
        
        return score, reasons
    
    def _check_mcc_rarity(self, transactions: List[Dict[str, Any]], target_tx: Dict[str, Any]) -> tuple[float, List[str]]:
        """Check for rare or unusual merchant category codes."""
        reasons = []
        score = 0.0
        
        try:
            target_mcc = target_tx.get("mcc")
            
            # High-risk MCCs
            high_risk_mccs = {
                "5967": "Direct marketing - inbound teleservices",
                "5966": "Direct marketing - outbound teleservices", 
                "7995": "Gambling transactions",
                "7273": "Dating services",
                "5912": "Drug stores and pharmacies (potential card testing)",
                "5122": "Drugs, drug proprietors (potential card testing)"
            }
            
            if target_mcc in high_risk_mccs:
                score = 85
                reasons.append(f"High-risk MCC {target_mcc}: {high_risk_mccs[target_mcc]}")
            
            # Check if MCC is rare for this customer
            mcc_counts = Counter([tx.get("mcc") for tx in transactions if tx.get("mcc")])
            if target_mcc and mcc_counts[target_mcc] == 1 and len(transactions) > 10:
                score = max(score, 40)
                reasons.append(f"Rare MCC for customer: {target_mcc}")
            
        except Exception as e:
            logger.warning(f"MCC check error: {e}")
        
        return score, reasons
    
    def _check_chargebacks(self, profile: Dict[str, Any], transactions: List[Dict[str, Any]]) -> tuple[float, List[str]]:
        """Check for prior chargebacks and disputes."""
        reasons = []
        score = 0.0
        
        try:
            chargeback_count = profile.get("chargeback_count", 0)
            dispute_count = profile.get("dispute_count", 0)
            
            if chargeback_count > 0:
                score = min(chargeback_count * 30, 100)
                reasons.append(f"Customer has {chargeback_count} prior chargeback(s)")
            
            if dispute_count > 2:
                score = max(score, 60)
                reasons.append(f"Customer has {dispute_count} prior dispute(s)")
            
        except Exception as e:
            logger.warning(f"Chargeback check error: {e}")
        
        return score, reasons
    
    def _check_amount_anomaly(self, transactions: List[Dict[str, Any]], target_tx: Dict[str, Any]) -> tuple[float, List[str]]:
        """Check if transaction amount is anomalous."""
        reasons = []
        score = 0.0
        
        try:
            target_amount = float(target_tx.get("amount", 0))
            amounts = [float(tx.get("amount", 0)) for tx in transactions if tx.get("id") != target_tx.get("id")]
            
            if not amounts:
                return 0.0, []
            
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            
            # Significantly larger than average
            if target_amount > avg_amount * 3 and target_amount > 100:
                score = 70
                reasons.append(f"Amount ${target_amount:.2f} is 3x average (${avg_amount:.2f})")
            elif target_amount > avg_amount * 2 and target_amount > 50:
                score = 40
                reasons.append(f"Amount ${target_amount:.2f} is 2x average (${avg_amount:.2f})")
            
            # Very large absolute amount
            if target_amount > 5000:
                score = max(score, 60)
                reasons.append(f"Large transaction amount: ${target_amount:.2f}")
            
        except Exception as e:
            logger.warning(f"Amount anomaly check error: {e}")
        
        return score, reasons
    
    def _check_location_change(self, transactions: List[Dict[str, Any]], target_tx: Dict[str, Any]) -> tuple[float, List[str]]:
        """Check for rapid location changes (impossible travel)."""
        reasons = []
        score = 0.0
        
        try:
            target_location = target_tx.get("merchant_city") or target_tx.get("merchant_state")
            target_country = target_tx.get("merchant_country", "US")
            
            # International transaction
            if target_country != "US":
                score = 50
                reasons.append(f"International transaction: {target_country}")
            
            # Check for rapid location changes
            if len(transactions) >= 2:
                prev_tx = transactions[1] if len(transactions) > 1 else transactions[0]
                prev_location = prev_tx.get("merchant_city") or prev_tx.get("merchant_state")
                prev_country = prev_tx.get("merchant_country", "US")
                
                if target_location and prev_location and target_location != prev_location:
                    # Calculate time difference
                    target_time = datetime.fromisoformat(target_tx.get("timestamp", "").replace('Z', '+00:00'))
                    prev_time = datetime.fromisoformat(prev_tx.get("timestamp", "").replace('Z', '+00:00'))
                    time_diff_hours = (target_time - prev_time).total_seconds() / 3600
                    
                    # Different countries in short time
                    if target_country != prev_country and time_diff_hours < 4:
                        score = max(score, 80)
                        reasons.append(f"Impossible travel: {prev_country} to {target_country} in {time_diff_hours:.1f} hours")
                    # Different cities in very short time
                    elif time_diff_hours < 1:
                        score = max(score, 60)
                        reasons.append(f"Rapid location change: {prev_location} to {target_location} in {time_diff_hours:.1f} hours")
            
        except Exception as e:
            logger.warning(f"Location check error: {e}")
        
        return score, reasons
    
    def _determine_action(self, risk_score: float, reasons: List[str]) -> tuple[str, str]:
        """Determine recommended action based on risk score."""
        if risk_score >= 80:
            return "freeze_card", "critical"
        elif risk_score >= 60:
            return "open_dispute", "high"
        elif risk_score >= 40:
            return "contact_customer", "medium"
        elif risk_score >= 20:
            return "review_manual", "low"
        else:
            return "approve", "minimal"
