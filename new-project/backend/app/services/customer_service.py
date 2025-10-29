"""Service for handling customer data and operations."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from collections import defaultdict
# Use package-relative imports to reference model modules within the app package
from ..models import Customer, Case, Transaction, Alert

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID."""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def list_customers(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List customers with pagination."""
        offset = (page - 1) * page_size
        
        # Get total count
        total = self.db.query(func.count(Customer.id)).scalar() or 0
        
        # Get paginated customers
        customers = self.db.query(Customer)\
                          .order_by(Customer.created_at.desc())\
                          .offset(offset)\
                          .limit(page_size)\
                          .all()
        
        return {
            "customers": customers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
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
    
    def get_customer_analytics(self, customer_id: str, days: int = 90) -> Dict[str, Any]:
        """Get comprehensive analytics for a customer."""
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = self.db.query(Transaction)\
            .filter(Transaction.customer_id == customer_id)\
            .filter(Transaction.ts >= start_date)\
            .order_by(desc(Transaction.ts))\
            .all()
        
        # Transaction Timeline - daily aggregation
        timeline = self._calculate_timeline(transactions)
        
        # Category Spend - group by MCC ranges
        category_spend = self._calculate_category_spend(transactions)
        
        # Merchant Mix - top merchants
        merchant_mix = self._calculate_merchant_mix(transactions)
        
        # Anomalies - suspicious patterns
        anomalies = self._detect_anomalies(customer_id, transactions)
        
        # Summary statistics
        total_amount = sum(t.amount_cents for t in transactions)
        avg_transaction = total_amount / len(transactions) if transactions else 0
        
        return {
            "timeline": timeline,
            "category_spend": category_spend,
            "merchant_mix": merchant_mix,
            "anomalies": anomalies,
            "summary": {
                "total_transactions": len(transactions),
                "total_amount_cents": total_amount,
                "avg_transaction_cents": int(avg_transaction),
                "period_days": days
            }
        }
    
    def _calculate_timeline(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Calculate daily transaction timeline."""
        daily_totals = defaultdict(int)
        daily_counts = defaultdict(int)
        
        for txn in transactions:
            date_key = txn.ts.strftime('%Y-%m-%d')
            daily_totals[date_key] += txn.amount_cents
            daily_counts[date_key] += 1
        
        # Sort by date and return
        timeline = []
        for date_str in sorted(daily_totals.keys()):
            timeline.append({
                "date": date_str,
                "amount_cents": daily_totals[date_str],
                "count": daily_counts[date_str]
            })
        
        return timeline
    
    def _calculate_category_spend(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Calculate spending by category (MCC ranges)."""
        # MCC category mapping (simplified)
        mcc_categories = {
            "Retail": range(5200, 5600),
            "Travel": range(3000, 4000),
            "Food & Dining": range(5400, 5500),
            "Entertainment": range(7800, 8000),
            "Services": range(7200, 7400),
        }
        
        category_totals = defaultdict(int)
        
        for txn in transactions:
            try:
                mcc_code = int(txn.mcc)
                categorized = False
                
                for category, mcc_range in mcc_categories.items():
                    if mcc_code in mcc_range:
                        category_totals[category] += txn.amount_cents
                        categorized = True
                        break
                
                if not categorized:
                    category_totals["Other"] += txn.amount_cents
            except (ValueError, TypeError):
                category_totals["Other"] += txn.amount_cents
        
        # Calculate total for percentages
        total = sum(category_totals.values())
        
        # Convert to list with percentages
        categories = []
        for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total * 100) if total > 0 else 0
            categories.append({
                "name": category,
                "amount_cents": amount,
                "percentage": round(percentage, 1)
            })
        
        return categories
    
    def _calculate_merchant_mix(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Calculate top merchants by spend."""
        merchant_totals = defaultdict(int)
        merchant_counts = defaultdict(int)
        
        for txn in transactions:
            merchant_totals[txn.merchant] += txn.amount_cents
            merchant_counts[txn.merchant] += 1
        
        # Get top 10 merchants
        top_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {
                "merchant": merchant,
                "total_cents": amount,
                "count": merchant_counts[merchant]
            }
            for merchant, amount in top_merchants
        ]
    
    def _detect_anomalies(self, customer_id: str, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Detect anomalies and suspicious patterns."""
        anomalies = []
        
        if not transactions:
            return anomalies
        
        # Calculate average transaction amount
        avg_amount = sum(t.amount_cents for t in transactions) / len(transactions)
        
        # Detect high-value transactions (3x average)
        threshold = avg_amount * 3
        high_value_txns = [t for t in transactions if t.amount_cents > threshold]
        
        for txn in high_value_txns[:5]:  # Limit to 5 most recent
            anomalies.append({
                "date": txn.ts.isoformat(),
                "type": "high_value",
                "description": f"Unusual high-value transaction at {txn.merchant}",
                "amount_cents": txn.amount_cents,
                "severity": "medium"
            })
        
        # Detect rapid transactions (multiple within 1 hour)
        sorted_txns = sorted(transactions, key=lambda t: t.ts)
        for i in range(len(sorted_txns) - 2):
            time_diff = (sorted_txns[i+2].ts - sorted_txns[i].ts).total_seconds()
            if time_diff < 3600:  # 1 hour
                anomalies.append({
                    "date": sorted_txns[i].ts.isoformat(),
                    "type": "rapid_transactions",
                    "description": f"Multiple transactions in quick succession",
                    "severity": "low"
                })
                break  # Only report once
        
        # Check for alerts associated with customer
        alerts = self.db.query(Alert)\
            .filter(Alert.customer_id == customer_id)\
            .filter(Alert.status != 'CLOSED')\
            .order_by(desc(Alert.created_at))\
            .limit(5)\
            .all()
        
        for alert in alerts:
            anomalies.append({
                "date": alert.created_at.isoformat(),
                "type": "alert",
                "description": f"System alert: {alert.risk} risk",
                "severity": alert.risk.lower() if alert.risk else "medium"
            })
        
        return anomalies