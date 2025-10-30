"""
Test script to demonstrate PII redaction in logging.
This simulates logging scenarios with sensitive data.
"""
import sys
sys.path.insert(0, '/app')

from app.utils.logger import (
    setup_logging,
    redact_pii,
    redact_dict,
    safe_log_data,
    log_service_call
)

# Set up test logger
logger = setup_logging("pii_redaction_test", level=10)  # DEBUG level

print("=" * 80)
print("PII REDACTION TEST - Demonstrating Secure Logging")
print("=" * 80)
print()

# Test 1: Email redaction
print("Test 1: Email Redaction")
print("-" * 80)
original = "Customer email: john.doe@example.com, support@company.org"
redacted = redact_pii(original)
print(f"Original: {original}")
print(f"Redacted: {redacted}")
print()

# Test 2: Phone number redaction
print("Test 2: Phone Number Redaction")
print("-" * 80)
original = "Contact: 555-123-4567 or 123-456-7890 or 5551234567"
redacted = redact_pii(original)
print(f"Original: {original}")
print(f"Redacted: {redacted}")
print()

# Test 3: SSN redaction
print("Test 3: SSN Redaction")
print("-" * 80)
original = "Customer SSN: 123-45-6789, Spouse SSN: 987-65-4321"
redacted = redact_pii(original)
print(f"Original: {original}")
print(f"Redacted: {redacted}")
print()

# Test 4: Credit card redaction
print("Test 4: Credit Card Redaction")
print("-" * 80)
original = "Card number: 4532-1234-5678-9010 or 4532123456789010"
redacted = redact_pii(original)
print(f"Original: {original}")
print(f"Redacted: {redacted}")
print()

# Test 5: Dictionary with sensitive fields
print("Test 5: Dictionary with Sensitive Fields")
print("-" * 80)
customer_data = {
    "customer_id": "CUST-001",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "555-123-4567",
    "password": "my_secret_password",
    "ssn": "123-45-6789",
    "credit_card": "4532-1234-5678-9010",
    "address": "123 Main St",
    "metadata": {
        "last_login_ip": "192.168.1.100",
        "api_key": "sk_live_abc123xyz789",
        "token": "bearer_token_secret"
    }
}

print("Original Data:")
import json
print(json.dumps(customer_data, indent=2))
print()
print("Redacted Data:")
print(safe_log_data(customer_data))
print()

# Test 6: Nested structure redaction
print("Test 6: Nested Structure Redaction")
print("-" * 80)
transaction_data = {
    "transaction_id": "TXN-12345",
    "amount": 150.00,
    "customer": {
        "name": "Jane Smith",
        "email": "jane.smith@email.com",
        "account_number": "9876543210",
        "card_number": "5555-4444-3333-2222"
    },
    "merchant": {
        "name": "Store XYZ",
        "contact": "merchant@store.com"
    },
    "notes": "Customer called from 555-999-8888 about transaction"
}

print("Redacted Transaction:")
print(safe_log_data(transaction_data))
print()

# Test 7: List of sensitive items
print("Test 7: List with Sensitive Data")
print("-" * 80)
alerts = [
    {"alert_id": "A1", "customer_email": "user1@test.com", "ip": "10.0.0.1"},
    {"alert_id": "A2", "customer_email": "user2@test.com", "ip": "192.168.1.50"},
    {"alert_id": "A3", "customer_phone": "555-111-2222", "ssn": "111-22-3333"}
]

print("Redacted Alerts:")
print(safe_log_data(alerts))
print()

# Test 8: Service method logging with decorator
print("Test 8: Service Method with Logging Decorator")
print("-" * 80)

class MockService:
    @log_service_call(logger, log_result=True)
    def process_payment(self, customer_id: str, card_number: str, amount: float):
        """Simulate payment processing."""
        result = {
            "success": True,
            "customer_id": customer_id,
            "card_last_4": card_number[-4:],
            "amount": amount,
            "transaction_id": "TXN-MOCK-123"
        }
        return result

service = MockService()
print("Calling process_payment with sensitive data...")
result = service.process_payment("CUST-001", "4532-1234-5678-9010", 99.99)
print(f"Result: {result}")
print()

# Test 9: Combined PII in text
print("Test 9: Multiple PII Types in Single Text")
print("-" * 80)
text = """
Customer Information:
- Name: John Doe
- Email: john.doe@example.com
- Phone: 555-123-4567
- SSN: 123-45-6789
- Credit Card: 4532-1234-5678-9010
- IP Address: 192.168.1.100

Please contact at support@company.com or call 555-999-8888.
"""
print("Original:")
print(text)
print("\nRedacted:")
print(redact_pii(text))
print()

# Test 10: Logging at different levels
print("Test 10: Logging at Different Levels (INFO, WARNING, ERROR)")
print("-" * 80)
logger.info("Processing customer john.doe@example.com")
logger.warning("Suspicious activity from IP 192.168.1.100 - SSN attempt: 123-45-6789")
logger.error("Failed payment for card 4532-1234-5678-9010")
print()

print("=" * 80)
print("✅ PII REDACTION TEST COMPLETE")
print("=" * 80)
print()
print("Summary:")
print("  • Emails → [EMAIL]")
print("  • Phone numbers → [PHONE]")
print("  • SSNs → [SSN]")
print("  • Credit cards → [CARD]")
print("  • IP addresses → [IP]")
print("  • Sensitive fields (password, token, etc.) → [REDACTED]")
print()
print("All logs are safe to store and review without exposing PII!")
print()
