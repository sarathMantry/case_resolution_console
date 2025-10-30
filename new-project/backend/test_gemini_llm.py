"""
Test script for Gemini LLM integration.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.gemini_llm import get_gemini_llm

def test_gemini_integration():
    """Test Gemini LLM integration."""
    print("🧪 Testing Gemini LLM Integration\n")
    
    llm = get_gemini_llm()
    
    if not llm.enabled:
        print("❌ Gemini LLM is not enabled (API key missing)")
        return False
    
    print(f"✅ Gemini LLM initialized")
    print(f"   Model: {llm.model_name}")
    print(f"   Temperature: {llm.temperature}")
    print(f"   Max Tokens: {llm.max_tokens}\n")
    
    # Test 1: Fraud Reasoning
    print("Test 1: Fraud Reasoning Generation")
    print("-" * 50)
    fraud_signals = {
        "signal_scores": {
            "velocity": 80,
            "device_change": 60,
            "mcc_rarity": 85
        },
        "reasons": [
            "High velocity: 7 transactions in last hour",
            "Recent device change detected",
            "High-risk MCC 7995: Gambling transactions"
        ]
    }
    
    transaction = {
        "amount": 500.00,
        "merchant_name": "Online Casino",
        "category": "gambling",
        "merchant_city": "Las Vegas",
        "merchant_country": "US",
        "timestamp": "2025-10-30T14:30:00Z"
    }
    
    profile = {
        "account_age_days": 30,
        "chargeback_count": 2,
        "dispute_count": 1,
        "account_status": "active"
    }
    
    reasoning = llm.generate_fraud_reasoning(fraud_signals, transaction, profile)
    print(f"Generated Reasoning:\n{reasoning}\n")
    
    # Test 2: Insights Summary
    print("Test 2: Insights Summary Generation")
    print("-" * 50)
    insights = {
        "transaction_count": 25,
        "spending_patterns": {
            "total_spent": 5000,
            "average_transaction": 200
        },
        "anomalies": [
            {
                "reasons": ["Amount exceeds 2σ threshold", "Unusual time: 3:00 AM"],
                "severity": "high"
            }
        ],
        "categories": {
            "top_categories": [["gambling", 10], ["shopping", 8]]
        },
        "merchants": {
            "merchant_concentration": 0.65
        }
    }
    
    summary = llm.generate_insights_summary(insights)
    print(f"Generated Summary:\n{summary}\n")
    
    # Test 3: Action Recommendation
    print("Test 3: Action Recommendation")
    print("-" * 50)
    recommendation = llm.generate_action_recommendation(
        risk_score=75.5,
        fraud_reasons=[
            "High velocity transactions",
            "Device change detected",
            "High-risk merchant category"
        ],
        compliance_status={
            "compliance_status": "non_compliant",
            "violations": [{"check": "otp_verification"}],
            "requirements": ["OTP verification required"]
        },
        kb_citations=[
            {
                "title": "High Velocity Transactions",
                "content": "Multiple transactions in short period indicate card testing..."
            }
        ]
    )
    
    if recommendation:
        print(f"Recommended Action: {recommendation['action']}")
        print(f"Reasoning:\n{recommendation['reasoning']}\n")
    
    # Test 4: Alert Description
    print("Test 4: Alert Description Enhancement")
    print("-" * 50)
    alert = {
        "risk_level": "high",
        "risk_score": 75.5,
        "customer_id": "cust_12345",
        "reasons": [
            "High velocity transactions",
            "Device change detected",
            "High-risk MCC"
        ],
        "proposed_action": "freeze_card"
    }
    
    description = llm.enhance_alert_description(alert)
    print(f"Enhanced Description:\n{description}\n")
    
    print("=" * 50)
    print("✅ All Gemini LLM tests completed successfully!")
    return True


if __name__ == "__main__":
    # Set API key from environment
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAZ_W83XXTyXnk6Fpp0D8_DeKvkKGW1iXc"
    
    try:
        success = test_gemini_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
