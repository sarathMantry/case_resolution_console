"""
Insights Agent: Analyzes transaction patterns, categories, and spending behavior.
"""

import time
from typing import Dict, Any, List
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ..utils.logger import setup_logging, log_service_call
from ..utils.gemini_llm import get_gemini_llm

logger = setup_logging("insights_agent")


class InsightsAgent:
    """
    Analyzes customer transaction patterns using deterministic rules.
    Identifies categories, merchant concentration, and spending patterns.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.timeout = 10  # seconds
        self.llm = get_gemini_llm()
    
    @log_service_call(logger)
    def analyze(self, customer_id: str, recent_transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze transaction patterns for insights.
        
        Args:
            customer_id: Customer identifier
            recent_transactions: List of recent transactions
            
        Returns:
            Dictionary containing insights and patterns
        """
        start_time = time.time()
        
        try:
            if not recent_transactions:
                return {
                    "success": False,
                    "error": "No transactions to analyze",
                    "duration": time.time() - start_time
                }
            
            # Calculate category distribution
            categories = self._analyze_categories(recent_transactions)
            
            # Calculate merchant concentration
            merchant_stats = self._analyze_merchants(recent_transactions)
            
            # Identify spending patterns
            spending_patterns = self._analyze_spending_patterns(recent_transactions)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(recent_transactions, spending_patterns)
            
            # Time-based patterns
            temporal_patterns = self._analyze_temporal_patterns(recent_transactions)
            
            result = {
                "success": True,
                "customer_id": customer_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "transaction_count": len(recent_transactions),
                "categories": categories,
                "merchants": merchant_stats,
                "spending_patterns": spending_patterns,
                "anomalies": anomalies,
                "temporal_patterns": temporal_patterns,
                "duration": time.time() - start_time
            }
            
            # Generate natural language summary using Gemini
            if self.llm.enabled:
                try:
                    result["llm_summary"] = self.llm.generate_insights_summary(result)
                except Exception as e:
                    logger.warning(f"LLM summary generation failed: {e}")
            
            logger.info(f"Insights analysis complete for customer {customer_id}: {len(anomalies)} anomalies detected")
            return result
            
        except Exception as e:
            logger.error(f"Error in insights analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _analyze_categories(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transaction category distribution."""
        categories = [tx.get("category", "Unknown") for tx in transactions]
        category_amounts = defaultdict(float)
        
        for tx in transactions:
            category = tx.get("category", "Unknown")
            amount = float(tx.get("amount", 0))
            category_amounts[category] += amount
        
        category_counts = Counter(categories)
        total_amount = sum(category_amounts.values())
        
        return {
            "distribution": dict(category_counts),
            "total_by_category": dict(category_amounts),
            "top_categories": category_counts.most_common(5),
            "category_concentration": max(category_counts.values()) / len(transactions) if transactions else 0,
            "dominant_category": category_counts.most_common(1)[0][0] if category_counts else None
        }
    
    def _analyze_merchants(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze merchant concentration and patterns."""
        merchants = [tx.get("merchant_name", "Unknown") for tx in transactions]
        merchant_counts = Counter(merchants)
        
        merchant_amounts = defaultdict(float)
        for tx in transactions:
            merchant = tx.get("merchant_name", "Unknown")
            amount = float(tx.get("amount", 0))
            merchant_amounts[merchant] += amount
        
        unique_merchants = len(set(merchants))
        
        return {
            "unique_count": unique_merchants,
            "top_merchants": merchant_counts.most_common(10),
            "merchant_concentration": max(merchant_counts.values()) / len(transactions) if transactions else 0,
            "repeat_merchant_ratio": (len(transactions) - unique_merchants) / len(transactions) if transactions else 0,
            "total_by_merchant": dict(merchant_amounts)
        }
    
    def _analyze_spending_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spending patterns and statistics."""
        amounts = [float(tx.get("amount", 0)) for tx in transactions]
        
        if not amounts:
            return {}
        
        amounts_sorted = sorted(amounts)
        n = len(amounts)
        
        return {
            "total_spent": sum(amounts),
            "average_transaction": sum(amounts) / n,
            "median_transaction": amounts_sorted[n // 2],
            "min_transaction": min(amounts),
            "max_transaction": max(amounts),
            "std_deviation": self._calculate_std(amounts),
            "large_transaction_count": sum(1 for a in amounts if a > 1000),
            "small_transaction_count": sum(1 for a in amounts if a < 10)
        }
    
    def _detect_anomalies(self, transactions: List[Dict[str, Any]], patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalous transactions based on patterns."""
        anomalies = []
        
        if not patterns:
            return anomalies
        
        avg_amount = patterns.get("average_transaction", 0)
        std_dev = patterns.get("std_deviation", 0)
        threshold = avg_amount + (2 * std_dev)  # 2 standard deviations
        
        for tx in transactions:
            amount = float(tx.get("amount", 0))
            reasons = []
            
            # Large amount anomaly
            if amount > threshold and std_dev > 0:
                reasons.append(f"Amount ${amount:.2f} exceeds 2σ threshold (${threshold:.2f})")
            
            # Unusual time anomaly
            tx_time = tx.get("timestamp")
            if tx_time:
                hour = datetime.fromisoformat(tx_time.replace('Z', '+00:00')).hour
                if hour < 5 or hour > 23:
                    reasons.append(f"Unusual transaction time: {hour}:00")
            
            # Foreign transaction
            if tx.get("is_international", False):
                reasons.append("International transaction")
            
            # High-risk MCC
            mcc = tx.get("mcc")
            high_risk_mccs = ["5967", "5966", "7995", "7273"]  # Cash advance, wire transfer, gambling, etc.
            if mcc in high_risk_mccs:
                reasons.append(f"High-risk merchant category: {mcc}")
            
            if reasons:
                anomalies.append({
                    "transaction_id": tx.get("id"),
                    "amount": amount,
                    "merchant": tx.get("merchant_name"),
                    "timestamp": tx.get("timestamp"),
                    "reasons": reasons,
                    "severity": "high" if len(reasons) >= 2 else "medium"
                })
        
        return anomalies
    
    def _analyze_temporal_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze time-based transaction patterns."""
        if not transactions:
            return {}
        
        hourly_distribution = defaultdict(int)
        daily_distribution = defaultdict(int)
        
        for tx in transactions:
            tx_time = tx.get("timestamp")
            if tx_time:
                try:
                    dt = datetime.fromisoformat(tx_time.replace('Z', '+00:00'))
                    hourly_distribution[dt.hour] += 1
                    daily_distribution[dt.strftime("%A")] += 1
                except:
                    pass
        
        return {
            "hourly_distribution": dict(hourly_distribution),
            "daily_distribution": dict(daily_distribution),
            "peak_hour": max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None,
            "peak_day": max(daily_distribution.items(), key=lambda x: x[1])[0] if daily_distribution else None
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
